import os
from datetime import datetime

import h2o
import mlflow
import mlflow.h2o
import pandas as pd
from sklearn.metrics import classification_report, f1_score

from utils import get_featured_j1_league


EXPT_BD = os.getenv("EXPT_BD")
EXPT_HC = os.getenv("EXPT_HC")

MODEL_BD_ENDPOINT = f"models:/{EXPT_BD}/{{}}"
MODEL_HC_ENDPOINT = f"models:/{EXPT_HC}/{{}}"


def evaluate_handicap_model(version: str) -> list[str, float, str]:
    clf_hc = mlflow.h2o.load_model(MODEL_HC_ENDPOINT.format(version))
    clf_bd = mlflow.h2o.load_model(MODEL_BD_ENDPOINT.format(version))
    
    curr_seas = datetime.now().year
    
    test = get_featured_j1_league() \
        .query(f"season == {curr_seas}") \
        .drop(columns="season")
    
    # step 1 prediction
    test_h2o = h2o.H2OFrame(test)
    
    prediction = clf_hc.predict(test_h2o)
    
    # step 2 prediction
    test_pred = prediction.as_data_frame()
    test_pred["probability"] = test_pred[["A", "H"]].max(axis=1)
    test_pred["actual"] = test.reset_index(drop=True)["res"]
    
    dscn_h2o = h2o.H2OFrame(test_pred[["predict", "probability"]])
    dscn_pred = clf_bd.predict(dscn_h2o)
    
    test_pred["decision"] = dscn_pred.as_data_frame()["predict"]
    
    pred = test_pred.query("decision == 1")
    y_hat = pred["predict"]
    y_true = pred["actual"]
    
    # metrics
    f1 = f1_score(y_true, y_hat, pos_label="H", average="macro")
    f1 = round(f1, 2)
    
    report = classification_report(y_true, y_hat)
    
    return [version, f1, report]


def evaluate_handicap_models(versions: list) -> dict:
    results = []
    for version in versions.split(","):
        result = evaluate_handicap_model(version)
        results.append(result)
    
    col = ["Version", "F1 Score", "report"]
    evaluation = pd.DataFrame(results, columns=col) \
        .to_dict()
    
    return evaluation
