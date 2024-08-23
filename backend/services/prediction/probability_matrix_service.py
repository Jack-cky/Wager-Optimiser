import numpy as np
import pandas as pd
from scipy.stats import poisson

from models import get_probability_matrix_predictor
from utils import get_team_mapping


def get_probability_matrix(home: str, away: str, max_goals: int) -> dict:
    glm = get_probability_matrix_predictor()
    
    encoder = get_team_mapping("encoder")
    
    home = encoder[home]
    away = encoder[away]
    
    col = ["team", "opponent", "stadium"]
    df_h = pd.DataFrame(data=[[home, away, 1]], columns=col)
    df_a = pd.DataFrame(data=[[away, home, 0]], columns=col)
    
    lambda_h = glm.predict(df_h).values[0]
    lambda_a = glm.predict(df_a).values[0]
    
    y_hat = [
        [poisson.pmf(goal, lambda_) for goal in range(0, max_goals+1)]
        for lambda_ in [lambda_h, lambda_a]
    ]
    
    Y = np.outer(np.array(y_hat[0]), np.array(y_hat[1]))
    
    prob_matrix = pd.DataFrame(Y) \
        .to_dict()
    
    return prob_matrix
