import os

import mlflow


EXPT_GP = os.getenv("EXPT_GP")
MODEL_ENDPOINT = f"models:/{EXPT_GP}@in_use"


def get_probability_matrix_predictor():
    glm = mlflow.statsmodels.load_model(MODEL_ENDPOINT)
    
    return glm
