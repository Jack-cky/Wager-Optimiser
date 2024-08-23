import h2o
import numpy as np
import pandas as pd

from models import get_handicap_predictors
from utils import get_team_mapping, get_predicting_features


def derive_odds(odds: tuple[float, float, float]) -> tuple[str, float]:
    odds_home, odds_draw, odds_away = odds
    
    odds_home = 1 / odds_home
    odds_draw = 1 / odds_draw
    odds_away = 1 / odds_away
    odds_total = sum([odds_home, odds_draw, odds_away])
    
    rate_mkt_h = odds_home / odds_total
    rate_mkt_a = odds_away / odds_total
    
    knwl_mkt_intel = np.select(
        [rate_mkt_h >= .4, rate_mkt_a >= .3],
        ["H", "A"],
        default="D",
    )
    
    rate_mkt_net = rate_mkt_h - rate_mkt_a
    
    return knwl_mkt_intel, rate_mkt_net


def get_handicap_results(
    home: str, away: str, time_frame: str,
    odds_home: float, odds_draw: float, odds_away: float,
) -> dict:
    clf_hc, clf_bd = get_handicap_predictors()
    
    encoder = get_team_mapping("encoder")
    
    col = [
        "home", "away",
        "rate_h2h_win", "rate_h2h_lose", "knwl_h2h",
        "rank_net", "scores_net",
        "rate_seas_win_net", "rate_seas_lose_net",
        "rating_seas_net", "rating_hist_net",
    ]
    df = get_predicting_features(col)
    
    home = encoder[home]
    away = encoder[away]
    
    odds = odds_home, odds_draw, odds_away
    knwl_mkt_intel, rate_mkt_net = derive_odds(odds)
    
    n_rest_day_net = 0
    
    # combine derived features with known in advance features
    X = df.query(f"home=='{home}' and away=='{away}'") \
        .drop(columns=["home", "away"]) \
        .iloc[0].to_dict()
    
    X.update({
        "time_frame": time_frame,
        "knwl_mkt_intel": knwl_mkt_intel,
        "rate_mkt_net": rate_mkt_net,
        "n_rest_day_net": n_rest_day_net,
    })
    
    # step 1 prediction
    game = pd.DataFrame(X, index=[0])
    game_h2o = h2o.H2OFrame(game)
    
    prediction = clf_hc.predict(game_h2o)
    
    # step 2 prediction
    game_pred = prediction.as_data_frame()
    game_pred["probability"] = game_pred[["A", "H"]].max(axis=1)
    
    dscn_h2o = h2o.H2OFrame(game_pred[["predict", "probability"]])
    dscn_pred = clf_bd.predict(dscn_h2o)
    
    game_pred["decision"] = dscn_pred.as_data_frame()["predict"]
    
    # obtain prediction
    y_hat = game_pred[["predict", "probability", "decision"]].iloc[0] \
        .to_dict()
    
    return y_hat
