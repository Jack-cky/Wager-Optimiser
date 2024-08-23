import os
from datetime import datetime

import h2o
import mlflow
import mlflow.h2o
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels
from h2o.automl import H2OAutoML

from utils import get_featured_goals, get_featured_j1_league


statsmodels.genmod.generalized_linear_model.SET_USE_BIC_LLF(True)

EXPT_BD = os.getenv("EXPT_BD")
EXPT_GP = os.getenv("EXPT_GP")
EXPT_HC = os.getenv("EXPT_HC")

TS_FORMAT = "%Y%m%d%H%M"
N_MODEL = 64


def get_j1_data(seas: int) -> tuple[str, list, h2o.H2OFrame, h2o.H2OFrame]:
    j1 = get_featured_j1_league()
    
    train = j1.query(f"season <= {seas-1}") \
        .drop(columns="season")
    
    dev = j1.query(f"season == {seas}") \
        .drop(columns="season")
    
    col_y = "res"
    col_x = [col for col in train.columns if col != col_y]
    
    train_h2o = h2o.H2OFrame(train)
    dev_h2o = h2o.H2OFrame(dev)
    
    train_h2o[col_y] = train_h2o[col_y].asfactor()
    
    return col_y, col_x, train_h2o, dev_h2o


def get_j1_predict_data(clf: H2OAutoML, dev_h2o: h2o.H2OFrame) -> h2o.H2OFrame:
    dev_pred = clf.predict(dev_h2o)
    
    train = dev_pred.as_data_frame()
    
    train["probability"] = train[["A", "H"]].max(axis=1)
    
    train["actual"] = dev_h2o.as_data_frame()["res"] \
        .reset_index(drop=True)
    
    train["correct"] = train["predict"] == train["actual"]
    train["correct"] = train["correct"].astype(int)
    
    train_h2o = h2o.H2OFrame(train)
    
    train_h2o["correct"] = train_h2o["correct"].asfactor()
    
    return train_h2o


def get_goals_data(seas: str) -> pd.DataFrame:
    col = ["season", "goals", "stadium", "team", "opponent"]
    
    df = get_featured_goals(col) \
        .query(f"season <= {seas}") \
        .drop(columns="season")
    
    return df


def train_handicap_model(seas: int) -> tuple[str, str]:
    def train_step_1_mode(seas: int) -> tuple[H2OAutoML, h2o.H2OFrame, str]:
        _ = mlflow.set_experiment(EXPT_HC)
        
        col_y, col_x, train_h2o, dev_h2o = get_j1_data(seas)
        
        dt = datetime.now().strftime(TS_FORMAT)
        
        with mlflow.start_run(run_name=f"hc_h2o_{dt}") as run:
            clf = H2OAutoML(
                max_models=N_MODEL,
                seed=42,
                balance_classes=True,
                sort_metric="logloss",
                exclude_algos=["DeepLearning"],
            )
            
            clf.train(
                x=col_x, y=col_y,
                training_frame=train_h2o,
                validation_frame=dev_h2o,
            )
            
            metrics = {
                "logloss": clf.leader.logloss(),
                "auc": clf.leader.auc(),
                "rmse": clf.leader.rmse(),
                "mse": clf.leader.mse()
            }
            
            mlflow.log_metrics(metrics)
            
            mlflow.h2o.log_model(
                clf.leader,
                 artifact_path="model",
                registered_model_name=EXPT_HC,
            )
            
            run_id = run.info.run_id
        
        return clf, dev_h2o, run_id
    
    def train_step_2_mode(clf_hc: H2OAutoML, dev_h2o: h2o.H2OFrame) -> str:
        _ = mlflow.set_experiment(EXPT_BD)
        
        train_h2o = get_j1_predict_data(clf_hc, dev_h2o)
        
        dt = datetime.now().strftime(TS_FORMAT)
        
        with mlflow.start_run(run_name=f"bd_h2o_{dt}") as run:
            clf_bd = H2OAutoML(
                max_models=N_MODEL,
                seed=42,
                balance_classes=True,
                sort_metric="logloss",
                exclude_algos=["DeepLearning"],
            )
            
            clf_bd.train(
                x=["predict", "probability"], y="correct",
                training_frame=train_h2o,
            )
            
            metrics = {
                "logloss": clf_bd.leader.logloss(),
                "auc": clf_bd.leader.auc(),
                "rmse": clf_bd.leader.rmse(),
                "mse": clf_bd.leader.mse()
            }
            
            mlflow.log_metrics(metrics)
            
            mlflow.h2o.log_model(
                clf_bd.leader,
                artifact_path="model",
                registered_model_name=EXPT_BD,
            )
            
            run_id = run.info.run_id
        
        return run_id
    
    clf, dev_h2o, run_id_hc = train_step_1_mode(seas)
    run_id_bd = train_step_2_mode(clf, dev_h2o)
    
    return run_id_hc, run_id_bd


def train_goals_probability_model(seas: int) -> str:
    _ = mlflow.set_experiment(EXPT_GP)
    
    df = get_goals_data(seas)
    
    dt = datetime.now().strftime(TS_FORMAT)
    
    with mlflow.start_run(run_name=f"gp_glm_{dt}") as run:
        mlflow.statsmodels.autolog(registered_model_name=EXPT_GP)
        
        glm = smf.glm(
            formula="goals ~ stadium + team + opponent",
            data=df,
            family=sm.families.Poisson()
        ).fit()
    
    run_id = run.info.run_id
    
    return run_id
