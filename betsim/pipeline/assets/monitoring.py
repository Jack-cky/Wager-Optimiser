from collections.abc import Iterator

import nannyml as nml
import pandas as pd
from dagster import AssetExecutionContext, Output, RetryPolicy, asset
from nannyml.thresholds import StandardDeviationThreshold

from betsim.pipeline.contracts import DriftDetection
from betsim.pipeline.resources import (
    DatabricksResource,
    GrafanaResource,
    MlflowResource,
    MySQLResource,
)
from betsim.shared.settings import MLflowConfig, SentinelConfig


def get_model_artefacts(mlflow: MlflowResource) -> tuple[list[str], list[str]]:
    model_version = mlflow.get_model_version(MLflowConfig.MODEL)
    artefacts = mlflow.load_artefacts(model_version.run_id)

    return artefacts["features"], artefacts["period_test"]


def split_reference_analysis(
    databricks: DatabricksResource,
    df: pd.DataFrame,
    period: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df.query(f"season != {SentinelConfig.SEASON}", inplace=True)
    df["time_frame"] = df["gdt"].str[:7]

    reference = df.query("@period[0] <= time_frame <= @period[1]").copy()
    analysis = df.query("time_frame > @period[1]").copy()

    for partition in (reference, analysis):
        partition.reset_index(drop=True, inplace=True)
        prediction = databricks.predict(partition)
        partition[["y_hat", "pi_hat"]] = prediction[["y_hat", "pi_hat"]]

    return reference, analysis


def detect_model_drift(
    reference: pd.DataFrame,
    analysis: pd.DataFrame,
    metrics: list[str],
    thresholds: dict[str, StandardDeviationThreshold] | None = None,
    chunk_period: str = "M",
) -> pd.DataFrame:
    calculator = nml.PerformanceCalculator(
        metrics=metrics,
        y_true="hcap_res",
        problem_type="classification_binary",
        y_pred="y_hat",
        y_pred_proba="pi_hat",
        timestamp_column_name="gdt",
        thresholds=thresholds,
        chunk_period=chunk_period,
    )
    calculator.fit(reference)

    return calculator.calculate(analysis).filter(period="analysis").to_df()


def log_performance(
    grafana: GrafanaResource,
    df: pd.DataFrame,
    metrics: list[str],
) -> None:
    for metric in metrics:
        grafana.push_metric(
            measurement="model_performance",
            stage="monitoring",
            field=metric,
            value=df.iloc[-1][(metric, "value")],
        )


def track_performance(
    grafana: GrafanaResource,
    reference: pd.DataFrame,
    analysis: pd.DataFrame,
) -> None:
    metrics = ["accuracy", "f1", "precision", "recall", "roc_auc"]
    df = detect_model_drift(reference, analysis, metrics, chunk_period="W-THU")

    log_performance(grafana, df, metrics)


def detect_data_drift(
    reference: pd.DataFrame,
    analysis: pd.DataFrame,
    features: list[str],
    threshold: StandardDeviationThreshold,
    chunk_period: str = "M",
) -> pd.DataFrame:
    calculator = nml.DataReconstructionDriftCalculator(
        column_names=features,
        timestamp_column_name="gdt",
        chunk_period=chunk_period,
        threshold=threshold,
    )
    calculator.fit(reference)

    return calculator.calculate(analysis).filter(period="analysis").to_df()


def get_metrics(df: pd.DataFrame) -> tuple[float, list[float], bool]:
    if not df.empty:
        out = df[["value", "upper_threshold", "lower_threshold"]].iloc[-1]
        val, ub, lb = (float(v) for v in out.values)
        is_flag = bool(df["alert"].any())
    else:
        val = ub = lb = None
        is_flag = False

    return val, [ub, lb], is_flag


def log_drift(grafana: GrafanaResource, result: dict[str, bool]) -> None:
    for field, flag in result.items():
        grafana.push_metric(
            measurement="drift_detection",
            stage="monitoring",
            field=field,
            value=float(flag),
        )


def track_degeneration(
    grafana: GrafanaResource,
    reference: pd.DataFrame,
    analysis: pd.DataFrame,
    features: list[str],
) -> dict[str, object]:
    threshold = StandardDeviationThreshold(
        std_lower_multiplier=2,
        std_upper_multiplier=2,
    )

    df = detect_model_drift(reference, analysis, ["f1"], {"f1": threshold})
    f1, thld_f1, is_model = get_metrics(df[1:-1]["f1"])

    df = detect_data_drift(reference, analysis, features, threshold)
    rec, thld_rec, is_data = get_metrics(df[1:-1]["reconstruction_error"])

    log_drift(grafana, {"model_drift": is_model, "data_drift": is_data})

    return {
        "observation": {
            "degeneration": is_model or is_data,
            "evidence": "model_drift" if is_model else "data_drift",
        },
        "model_drift": {
            "value": f1,
            "thresholds": thld_f1,
            "is_drift": is_model,
        },
        "data_drift": {
            "value": rec,
            "thresholds": thld_rec,
            "is_drift": is_data,
        }
    }


@asset(
    name="detection",
    description=(
        "Detects model and data drift with NannyML and pushes the "
        "metrics to Grafana."
    ),
    group_name="Monitoring",
    output_required=False,
    retry_policy=RetryPolicy(max_retries=3, delay=30),
    deps=["tables"],
)
def monitor_drift(
    context: AssetExecutionContext,
    databricks: DatabricksResource,
    grafana: GrafanaResource,
    mlflow: MlflowResource,
    mysql: MySQLResource,
) -> Iterator[Output[DriftDetection]]:
    jleague = mysql.read("jleague")
    features, period = get_model_artefacts(mlflow)
    reference, analysis = split_reference_analysis(databricks, jleague, period)

    track_performance(grafana, reference, analysis)
    summary = track_degeneration(grafana, reference, analysis, features)

    if not summary["observation"]["degeneration"]:
        context.log.info(
            "No performance degeneration detected as of "
            f"{analysis.time_frame.max()}."
        )
        return

    context.log.info(
        f"Detected {summary['observation']['evidence'].split('_')[0]} drift "
        f"on {analysis.time_frame.max()}."
    )

    yield Output(
        DriftDetection(evidence=summary["observation"]["evidence"]),
        metadata=summary,
    )
