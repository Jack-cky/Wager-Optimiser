from datetime import date

import mlflow
import pandas as pd
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient

from .training_service import submit_train_job


def train_initial_model(expt: str) -> pd.DataFrame:
    seas = date.today().year - 1
    submit_train_job(expt, seas, False)
    runs = mlflow.search_runs(run_view_type=ViewType.ACTIVE_ONLY)
    
    return runs


def get_leadboard(expt: str, metric: str) -> dict:
    client = MlflowClient()
    
    _ = mlflow.set_experiment(expt)
    
    runs = mlflow.search_runs(run_view_type=ViewType.ACTIVE_ONLY)
    
    if not len(runs):
        runs = train_initial_model(expt)
    
    runs["dt"] = runs["tags.mlflow.runName"].str[-12:]
    runs["Trained at"] = pd.to_datetime(runs["dt"], format="%Y%m%d%H%M") \
        .dt.strftime("%Y/%m/%d %H:%M")
    runs[f"{metric.upper()}"] = runs[f"metrics.{metric}"].round(2)
    runs = runs[["run_id", "Trained at", metric.upper()]].copy()
    
    data = [
        (model.version, model.aliases, model.run_id, model.tags["season"])
        for model in client.search_model_versions(f"name='{expt}'")
    ]
    smy = pd.DataFrame(data, columns=["Version", "In Use", "run_id", "Season"])
    smy["In Use"] = smy["In Use"].str.len() == 1
    
    smy = smy.merge(runs) \
        .assign(option=False) \
        .to_dict()
    
    return smy
