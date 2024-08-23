import h2o
import mlflow
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient


def assign_prod_alias(run_id: str) -> None:
    client = MlflowClient()
    
    model = client.search_model_versions(f"run_id='{run_id}'")[0]
    
    ver = model.version
    expt = model.name
    
    client.set_registered_model_alias(expt, "in_use", ver)


def assign_tags(run_id: str, season: int, expt: str, is_latest: bool) -> None:
    season = "Latest" if is_latest else season
    
    client = MlflowClient()
    client.set_tag(run_id, "season", season)
    
    ver = client.search_model_versions(f"run_id='{run_id}'")[0].version
    client.set_model_version_tag(expt, ver, "season", season)


def create_experiment(expt: str) -> None:
    if not mlflow.search_experiments(filter_string=f"name LIKE '{expt}'"):
        mlflow.create_experiment(expt)


def is_best_run(expt: str, run_id: str, metric: str) -> bool:
    _ = mlflow.set_experiment(expt)
    
    runs = mlflow.search_runs(run_view_type=ViewType.ALL)
    
    best_run_id = runs.sort_values(by=f"metrics.{metric}").iloc[0]["run_id"]
    
    is_best = best_run_id == run_id
    
    return is_best


def start_client_server() -> None:
    _ = MlflowClient()
    h2o.init()
