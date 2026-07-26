import numpy as np
import pandas as pd
from dagster import ConfigurableResource
from mlflow.deployments import get_deploy_client


class DatabricksResource(ConfigurableResource):
    endpoint: str
    host: str
    token: str

    def get_client(self):
        return get_deploy_client("databricks")

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.replace({np.nan: None}).to_dict(orient="split")
        response = self.get_client().predict(
            endpoint=self.endpoint,
            inputs={"dataframe_split": data},
        )
        return pd.DataFrame(response["predictions"])

    def get_endpoint_readiness(self) -> bool:
        endpoint = self.get_client().get_endpoint(self.endpoint)
        state = endpoint["state"]
        status = False

        match state["ready"], state["config_update"]:
            case ("FAILED", _) | (_, "UPDATE_FAILED"):
                raise RuntimeError(
                    f"Serving endpoint is in a failed state: {state}"
                )
            case ("NOT_READY", _) | (_, "IN_PROGRESS"):
                status = False
            case ("READY", "NOT_UPDATING"):
                status = True

        return status

    def update_endpoint(self, model_uc: str, version: str) -> None:
        self.get_client().update_endpoint_config(
            endpoint=self.endpoint,
            config={
                "served_entities": [{
                    "entity_name": model_uc,
                    "entity_version": version,
                    "workload_size": "Small",
                    "workload_type": "CPU",
                    "scale_to_zero_enabled": True,
                }],
            },
        )
