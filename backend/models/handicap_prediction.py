import os

import mlflow.h2o


EXPT_HC = os.getenv("EXPT_HC")
EXPT_BD = os.getenv("EXPT_BD")

MODEL_HC_ENDPOINT = f"models:/{EXPT_HC}@in_use"
MODEL_BD_ENDPOINT = f"models:/{EXPT_BD}@in_use"


def get_handicap_predictors():
    clf_hc = mlflow.h2o.load_model(MODEL_HC_ENDPOINT)
    clf_bd = mlflow.h2o.load_model(MODEL_BD_ENDPOINT)
    
    return clf_hc, clf_bd
