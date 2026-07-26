import json

import mlflow
import pandas as pd
from dagster import ConfigurableResource, InitResourceContext
from mlflow import MlflowClient


class MlflowResource(ConfigurableResource):
    catalog: str
    dependencies: list[str]
    experiment: str
    registry_uri: str
    tracking_uri: str
    uc_schema: str

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self.configure()

    def configure(self) -> None:
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_registry_uri(self.registry_uri)
        mlflow.set_experiment(self.experiment)

    def get_client(self) -> MlflowClient:
        return MlflowClient()

    def get_model_uc(self, model_name: str) -> str:
        return ".".join([self.catalog, self.uc_schema, model_name])

    def get_model_version(
        self,
        name: str,
        alias: str = "champion",
    ) -> mlflow.entities.model_registry.ModelVersion:
        return self.get_client().get_model_version_by_alias(
            name=self.get_model_uc(name),
            alias=alias,
        )

    def download_artefact(self, run_id: str, artefact: str) -> str:
        return mlflow.artifacts.download_artifacts(
            run_id=run_id,
            artifact_path=artefact,
        )

    def load_artefacts(self, run_id: str) -> dict[str, object]:
        pth = self.download_artefact(run_id, "model_artefacts.json")
        with open(pth, "r") as f:
            artefacts = json.load(f)
        return artefacts

    def start_run(self, run_name: str):
        return mlflow.start_run(run_name=run_name)

    def set_tag(self, key: str, value: str) -> None:
        mlflow.set_tag(key, value)

    def log_dict(self, payload: dict[str, object], artefact: str) -> None:
        mlflow.log_dict(payload, artefact)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        mlflow.log_metrics(metrics)

    def log_params(self, params: dict[str, object]) -> None:
        mlflow.log_params(params)

    def log_text(self, text: str, artefact: str) -> None:
        mlflow.log_text(text, artefact)

    def log_figure(self, figure, artefact: str) -> None:
        mlflow.log_figure(figure, artefact)

    def log_model(
        self,
        name: str,
        pyfunc_model,
        artifacts: dict[str, str],
        signature,
        input_example: pd.DataFrame,
    ) -> mlflow.entities.model_registry.ModelVersion:
        return mlflow.pyfunc.log_model(
            name=name,
            python_model=pyfunc_model,
            artifacts=artifacts,
            registered_model_name=self.get_model_uc(name),
            signature=signature,
            input_example=input_example,
            pip_requirements=self.dependencies,
        )

    def set_alias(self, model_name: str, version: str, alias: str) -> None:
        self.get_client().set_registered_model_alias(
            name=self.get_model_uc(model_name),
            version=version,
            alias=alias,
        )

    def load_model(self, model_name: str, alias: str = "challenger"):
        return mlflow.pyfunc.load_model(
            f"models:/{self.get_model_uc(model_name)}@{alias}"
        )
