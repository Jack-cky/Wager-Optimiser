import time
from dagster import AssetExecutionContext, Failure, RetryPolicy, asset

from betsim.pipeline.contracts import ModelEvaluation
from betsim.pipeline.resources import DatabricksResource, MlflowResource
from betsim.shared.settings import MLflowConfig, TimeoutConfig


@asset(
    name="endpoint",
    description=(
        "Deploys the current champion model to the configured "
        "Databricks serving endpoint."
    ),
    group_name="Deployment",
    retry_policy=RetryPolicy(max_retries=3, delay=30),
)
def deploy_model(
    context: AssetExecutionContext,
    databricks: DatabricksResource,
    mlflow: MlflowResource,
    evaluation: ModelEvaluation,
) -> None:
    waited = 0
    try:
        while not databricks.get_endpoint_readiness():
            if waited >= TimeoutConfig.ENDPOINT_READY:
                raise TimeoutError(
                    "Serving endpoint did not become ready within "
                    f"{TimeoutConfig.ENDPOINT_READY}s."
                )
            context.log.info("Waiting for serving endpoint to be ready...")
            time.sleep(TimeoutConfig.ENDPOINT_POLL)
            waited += TimeoutConfig.ENDPOINT_POLL
    except RuntimeError as e:
        raise Failure(description=str(e), allow_retries=False) from e

    databricks.update_endpoint(
        mlflow.get_model_uc(MLflowConfig.MODEL),
        evaluation.champion_version,
    )

    context.log.info("Deployment finished.")
