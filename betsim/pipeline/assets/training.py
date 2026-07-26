import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from tempfile import TemporaryDirectory

import cloudpickle
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import seaborn as sns
import xgboost as xgb
from dagster import AssetExecutionContext, Output, RetryPolicy, asset
from matplotlib.figure import Figure
from mlflow.models import infer_signature
from mlflow.pyfunc import PyFuncModel, PythonModel
from mrmr import mrmr_classif
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    fbeta_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

from betsim.pipeline.contracts import (
    DriftDetection,
    ModelEvaluation,
    TrainingResult,
)
from betsim.pipeline.resources import (
    DatabricksResource,
    MlflowResource,
    MySQLResource,
)
from betsim.shared.settings import MLflowConfig, SentinelConfig

cloudpickle.register_pickle_by_value(sys.modules[__name__])
optuna.logging.set_verbosity(optuna.logging.WARNING)


class XgbPyFuncModel(PythonModel):
    def __init__(self, exp_vars: list[str], boundary: list[float]):
        self.exp_vars = exp_vars
        self.lb, self.ub = boundary

    def load_context(self, context) -> None:
        self.model = xgb.XGBClassifier()
        self.model.load_model(context.artifacts["xgb_model"])

    def predict(self, context, model_input: pd.DataFrame) -> pd.DataFrame:
        model_input = model_input.loc[:, self.exp_vars]

        y_hat = self.model.predict(model_input)
        pi_hat = self.model.predict_proba(model_input)[:, 1]
        is_bet = (pi_hat < self.lb) | (pi_hat > self.ub)

        return pd.DataFrame({
            "y_hat": y_hat,
            "pi_hat": pi_hat,
            "is_bet": is_bet,
        })


def split_datasets(
    df: pd.DataFrame,
    delta: int = -6,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    tuple[np.ndarray, np.ndarray, np.ndarray],
]:
    df.query(f"season != {SentinelConfig.SEASON}", inplace=True)
    df["time_frame"] = df["gdt"].str[:7]

    frames = sorted(df["time_frame"].unique())
    period = frames[:3*delta], frames[3*delta:delta], frames[delta:]

    train = df.query("time_frame in @period[0]").reset_index(drop=True)
    dev = df.query("time_frame in @period[1]").reset_index(drop=True)
    test = df.query("time_frame in @period[2]").reset_index(drop=True)

    return train, dev, test, period


def select_features(df: pd.DataFrame, k: int = 10) -> tuple[str, list[str]]:
    resp_var = "hcap_res"
    exp_vars = [
        "rate_h2h_win", "rate_h2h_lose", "hcap_mag", "n_rest_day_net",
        "rate_seas_win_net", "rate_seas_lose_net", "scores_net", "rank_net",
        "rating_seas_net", "rating_hist_net", "xg_net", "xg_sup",
        "xg_h2h_win", "xg_h2h_lose",
    ]

    return resp_var, mrmr_classif(X=df[exp_vars], y=df[resp_var], K=k)


def prepare_datasets(
    df: pd.DataFrame,
) -> tuple[
    tuple[pd.DataFrame, pd.Series],
    tuple[pd.DataFrame, pd.Series],
    tuple[np.ndarray, np.ndarray, np.ndarray],
]:
    train, dev, _, period = split_datasets(df)
    resp_var, exp_vars = select_features(train)

    X_train, y_train = train[exp_vars], train[resp_var]
    X_dev, y_dev = dev[exp_vars], dev[resp_var]

    return (X_train, y_train), (X_dev, y_dev), period


def tune_hyperparameters(
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    n_trials: int = 50,
    scoring: str = "neg_log_loss",
    seed: int = 42,
) -> dict[str, object]:
    base_params = {
        "eval_metric": "logloss",
        "n_jobs": 1,
        "objective": "binary:logistic",
        "random_state": seed,
    }

    def objective(trial: optuna.Trial) -> float:
        clf = xgb.XGBClassifier(**{
            **base_params,
            "colsample_bytree": trial.suggest_float(
                "colsample_bytree", 0.6, 1.0,
            ),
            "gamma": trial.suggest_float("gamma", 1e-8, 5.0, log=True),
            "learning_rate": trial.suggest_float(
                "learning_rate", 0.01, 0.3, log=True,
            ),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "reg_alpha": trial.suggest_float(
                "reg_alpha", 1e-8, 10.0, log=True,
            ),
            "reg_lambda": trial.suggest_float(
                "reg_lambda", 1e-8, 10.0, log=True,
            ),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        })

        cv = StratifiedKFold(
            n_splits=n_splits,
            shuffle=True,
            random_state=seed,
        )

        score = cross_val_score(clf, X, y, cv=cv, scoring=scoring, n_jobs=-1)

        return -score.mean()

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=seed),
        study_name=f"{MLflowConfig.MODEL}_tuning",
    )
    study.optimize(objective, n_trials=n_trials)

    return {**base_params, **study.best_params}


def tag_experiment(mlflow: MlflowResource, evidence: str) -> None:
    mlflow.set_tag("model_family", "xgboost")
    mlflow.set_tag("trigger", evidence)


def fit_model(
    X: pd.DataFrame,
    y: pd.Series,
    params: dict[str, object],
) -> xgb.XGBClassifier:
    clf = xgb.XGBClassifier(**params)
    clf.fit(X, y, verbose=False)
    return clf


def get_prediction(
    clf: xgb.XGBClassifier | PyFuncModel | DatabricksResource,
    X: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    match clf:
        case xgb.XGBClassifier():
            y_hat = clf.predict(X)
            pi_hat = clf.predict_proba(X)[:, 1]
        case PyFuncModel() | DatabricksResource():
            prediction = clf.predict(X)
            y_hat = prediction["y_hat"]
            pi_hat = prediction["pi_hat"]

    return y_hat, pi_hat


def get_artefacts(
    target: str,
    features: list[str],
    period_train: pd.Series,
    period_test: pd.Series,
) -> dict[str, object]:
    return {
        "target": target,
        "features": features,
        "period_train": [period_train[0], period_train[-1]],
        "period_test": [period_test[0], period_test[-1]],
    }


def evaluate_model(
    y_true: np.ndarray,
    y_hat: np.ndarray,
    pi_hat: np.ndarray,
) -> dict[str, float]:
    boundary = pd.DataFrame({
        "correct": y_hat == y_true,
        "pi_hat_away": 1 - pi_hat,
        "pi_hat_home": pi_hat,
    }).query("correct").describe()

    metrics = {
        "accuracy": accuracy_score(y_true, y_hat),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_hat),
        "f05_score": fbeta_score(y_true, y_hat, beta=0.5),
        "f1_score": fbeta_score(y_true, y_hat, beta=1.0),
        "f2_score": fbeta_score(y_true, y_hat, beta=2.0),
        "log_loss": log_loss(y_true, pi_hat),
        "mcc": matthews_corrcoef(y_true, y_hat),
        "precision": precision_score(y_true, y_hat),
        "recall": recall_score(y_true, y_hat),
        "roc_auc": roc_auc_score(y_true, pi_hat),
        "boundary_away": boundary["pi_hat_away"]["25%"],
        "boundary_home": boundary["pi_hat_home"]["75%"],
    }

    return {k: float(v) for k, v in metrics.items()}


def report_classification(y_true: np.ndarray, y_hat: np.ndarray) -> str:
    return classification_report(
        y_true,
        y_hat,
        target_names=["Away", "Home"],
        digits=4,
    )


@contextmanager
def plot_matrix(y_true: np.ndarray, y_hat: np.ndarray) -> Iterator[Figure]:
    fig, ax = plt.subplots()
    try:
        cm = confusion_matrix(y_true, y_hat)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title("Confusion Matrix")
        ax.set_xticks([0.5, 1.5])
        ax.set_xticklabels(["Away", "Home"])
        ax.set_yticks([0.5, 1.5])
        ax.set_yticklabels(["Away", "Home"])
        yield fig
    finally:
        plt.close(fig)


@contextmanager
def plot_importance(ft: list[str], importance: np.ndarray) -> Iterator[Figure]:
    fig, ax = plt.subplots()
    try:
        ft_import = pd.DataFrame({"feature": ft, "importance": importance}) \
            .sort_values(by="importance", ascending=True)
        ax.barh(ft_import["feature"], ft_import["importance"])
        ax.set_xlabel("Importance")
        ax.set_title("Feature Importance")
        fig.tight_layout()
        yield fig
    finally:
        plt.close(fig)


def log_artefacts(
    mlflow: MlflowResource,
    target: str,
    features: list[str],
    period_train: np.ndarray,
    period_dev: np.ndarray,
    X: pd.DataFrame,
    y_true: np.ndarray,
    y_hat: np.ndarray,
    pi_hat: np.ndarray,
    clf: xgb.XGBClassifier,
    params: dict[str, object],
) -> str:
    artefacts = get_artefacts(target, features, period_train, period_dev)
    mlflow.log_dict(artefacts, "model_artefacts.json")

    metrics = evaluate_model(y_true, y_hat, pi_hat)
    lb, ub = metrics["boundary_away"], metrics["boundary_home"]
    mlflow.log_metrics(metrics)

    mlflow.log_params(params)

    report = report_classification(y_true, y_hat)
    mlflow.log_text(report, "classification_report.txt")

    with plot_matrix(y_true, y_hat) as fig:
        mlflow.log_figure(fig, "plots/confusion_matrix.png")

    with plot_importance(features, clf.feature_importances_) as fig:
        mlflow.log_figure(fig, "plots/feature_importance.png")

    signature = pd.DataFrame({
        "y_hat": y_hat,
        "pi_hat": pi_hat,
        "is_bet": (pi_hat < lb) | (pi_hat > ub),
    })

    with TemporaryDirectory() as tmp_dir:
        pth_model = f"{tmp_dir}/xgb_model.ubj"
        clf.save_model(pth_model)

        info = mlflow.log_model(
            name=MLflowConfig.MODEL,
            pyfunc_model=XgbPyFuncModel(exp_vars=features, boundary=[lb, ub]),
            artifacts={"xgb_model": pth_model},
            signature=infer_signature(X, signature),
            input_example=X.head(),
        )

    return info.registered_model_version


def log_run(
    mlflow: MlflowResource,
    period_train: np.ndarray,
    period_dev: np.ndarray,
    X_dev: pd.DataFrame,
    y_dev: pd.Series,
    clf: xgb.XGBClassifier,
    params: dict[str, object]
):
    vars = y_dev.name, X_dev.columns.tolist()
    pred = get_prediction(clf, X_dev)

    return log_artefacts(
        mlflow,
        *vars,
        period_train,
        period_dev,
        X_dev,
        y_dev,
        *pred,
        clf,
        params,
    )


def run_experiment(
    mlflow: MlflowResource,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_dev: pd.DataFrame,
    y_dev: pd.Series,
    params: dict[str, object],
    period: tuple[np.ndarray, np.ndarray, np.ndarray],
    evidence: str,
) -> dict[str, object]:
    dt = datetime.now().strftime("%Y%m%d%H%M")
    with mlflow.start_run(run_name=f"{MLflowConfig.MODEL}_{dt}") as run:
        tag_experiment(mlflow, evidence)
        clf = fit_model(X_train, y_train, params)
        version = log_run(mlflow, *period[:2], X_dev, y_dev, clf, params)

    mlflow.set_alias(MLflowConfig.MODEL, version, "challenger")

    return {"model_version": version, **run.to_dictionary()["info"]}


@asset(
    name="challenger",
    description=(
        "Trains and registers a new XGBoost challenger model from the "
        "feature table."
    ),
    group_name="Training",
    retry_policy=RetryPolicy(max_retries=3, delay=30),
)
def train_candidate_model(
    context: AssetExecutionContext,
    mlflow: MlflowResource,
    mysql: MySQLResource,
    detection: DriftDetection,
) -> Output[TrainingResult]:
    jleague = mysql.read("jleague")
    train, dev, period = prepare_datasets(jleague)
    params = tune_hyperparameters(*train)
    evidence = detection.evidence
    summary = run_experiment(mlflow, *train, *dev, params, period, evidence)

    context.log.info(
        f"Trained a model with development period from {period[1][0]} "
        f"to {period[1][-1]}."
    )

    return Output(
        TrainingResult(version=summary["model_version"]),
        metadata=summary,
    )


def prepare_artefacts(
    mlflow: MlflowResource,
    df: pd.DataFrame,
) -> tuple[xgb.XGBClassifier, pd.DataFrame, np.ndarray]:
    _, _, test, period = split_datasets(df)
    clf = mlflow.load_model(MLflowConfig.MODEL)

    return clf, test, period[2]


def evaluate_candidates(
    databricks: DatabricksResource,
    clf: xgb.XGBClassifier,
    test: pd.DataFrame,
    target: str = "hcap_res",
) -> tuple[dict[str, float], dict[str, float]]:
    champion = get_prediction(databricks, test)
    challenger = get_prediction(clf, test)

    metrics_cham = evaluate_model(test[target], *champion)
    metrics_chal = evaluate_model(test[target], *challenger)

    return metrics_cham, metrics_chal


def compare_performance(
    champion: dict[str, float],
    challenger: dict[str, float],
    epsilon_fbeta: float = 0.04,
    epsilon_logloss: float = 0.04,
) -> dict[str, object]:
    return {
        "is_promotable": (
            (challenger["f05_score"] >= champion["f05_score"] + epsilon_fbeta)
            or
            (challenger["log_loss"] <= champion["log_loss"] - epsilon_logloss)
            or (
                champion["f05_score"] - challenger["f05_score"]
                <= epsilon_fbeta
                and challenger["log_loss"] < champion["log_loss"]
            )
        ),
        **{f"champion_{k}": v for k, v in champion.items()},
        **{f"challenger_{k}": v for k, v in challenger.items()},
    }


@asset(
    name="evaluation",
    description=(
        "Compares the challenger against the champion and promotes it "
        "on improvement."
    ),
    group_name="Training",
    output_required=False,
    retry_policy=RetryPolicy(max_retries=3, delay=30),
)
def compare_model_performance(
    context: AssetExecutionContext,
    databricks: DatabricksResource,
    mlflow: MlflowResource,
    mysql: MySQLResource,
    challenger: TrainingResult,
) -> Iterator[Output[ModelEvaluation]]:
    jleague = mysql.read("jleague")
    clf, test, period = prepare_artefacts(mlflow, jleague)

    metrics = evaluate_candidates(databricks, clf, test)
    summary = compare_performance(*metrics)

    if not summary["is_promotable"]:
        context.log.info(
            f"Challenger model underperformed in the test period from "
            f"{period[0]} to {period[-1]}."
        )
        return

    mlflow.set_alias(MLflowConfig.MODEL, challenger.version, "champion")

    context.log.info(
        f"Promoted challenger model to champion for test period {period[0]} "
        f"to {period[-1]}."
    )

    yield Output(
        ModelEvaluation(champion_version=challenger.version),
        metadata=summary,
    )
