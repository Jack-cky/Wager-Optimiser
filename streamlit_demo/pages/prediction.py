from datetime import date
import json
import re

import h2o
import mlflow
import mlflow.h2o
import numpy as np
import pandas as pd
from scipy.stats import poisson
import streamlit as st

from utils import st_current_date_time, st_message_box, st_row_spacing, st_subtitle_centre


MSG_BTN_DISABLE = "Function is disabled in demo."


def st_team_selection(seas: int=date.today().year) -> tuple[str, str]:
    def show_team_img(team: str) -> None:
        if team:
            with st.columns(5)[2]:
                st.image("./frontend/static/imgs/team/moto.png", use_column_width=True)
    
    df = pd.read_parquet("./data/mapping/teams.parquet")
    
    teams = df.query(f"season == {seas}")["team"] \
        .tolist()
    
    div_home, _, div_away = st.columns((1, .5, 1))
    
    with div_home:
        home = st.selectbox("Home Team", teams, index=None)
        show_team_img(home)
    
    with div_away:
        away = st.selectbox("Away Team", teams, index=None)
        show_team_img(away)
    
    return home, away


def st_recent_games(home: str, away: str) -> None:
    def get_recent_games(team: str, n_games: int=5) -> str:
        MARKS = {3: "🟢", 1: "🟡", 0: "🔴"}
        
        with open("./data/mapping/encoder.json") as file:
            encoder = json.load(file)
        
        df = pd.read_parquet("./data/cleansed/plays.parquet")[["team", "points"]]
        
        results = df.query(f"team == '{encoder[team]}'")["points"] \
            .tail(n_games) \
            .map(MARKS) \
            .to_list()[::-1]
        
        results = re.sub(r"[\[\],']", "", str(results))
        
        return results
    
    def show_results(team: str, results: str) -> None:
        st.caption(team)
        
        st_subtitle_centre(results, "font-size: 30px;")
    
    st_subtitle_centre("Recent 5 Games (Left for Most Recent)")
    
    div_home, _, div_away = st.columns((1, .5, 1))
    
    if home:
        with div_home:
            results = get_recent_games(home)
            show_results(home, results)
    
    if away:
        with div_away:
            results = get_recent_games(away)
            show_results(away, results)


def st_season_summary(home: str, away: str) -> None:
    def get_seasonal_summary(home: str, away: str) -> dict:
        with open("./data/mapping/encoder.json") as file:
            encoder = json.load(file)
        with open("./data/mapping/decoder.json") as file:
            decoder = json.load(file)
        
        df = pd.read_parquet("./data/featured/plays.parquet")[["team", "rank", "scores", "rate_seas_win"]]
        
        home = home if home else "None"
        away = away if away else "None"
        
        smy = df.query(f"team == '{encoder[home]}' or team == '{encoder[away]}'") \
            .groupby("team", as_index=False) \
            .last()
        
        smy["idx"] = np.where(smy["team"] == encoder[home], 0, 1)
        smy["team"] = smy["team"].map(decoder)
        smy["rate_seas_win"] *= 100
        
        smy = smy.sort_values(by="idx") \
            .drop(columns="idx") \
            .rename(columns={
                "team": "Team", "rank": "Rank",
                "scores": "Scores", "rate_seas_win": "Win Rate (%)",
            }) \
            .set_index("Team") \
            .to_dict()
        
        return smy
    
    st_subtitle_centre("Seasonal Summary")
    
    response = get_seasonal_summary(home, away)
    
    smy = pd.DataFrame() \
        .from_dict(response) \
        .style.format("{:.1f}%", "Win Rate (%)")
    
    st.dataframe(smy, use_container_width=True)


def st_elo_rating(home: str, away: str, seas: int=date.today().year) -> None:
    def query_seas_elo(team: str, df: pd.DataFrame, mt: dict) -> pd.DataFrame:
        elo = df.query(f"team == '{mt[team]}'")[["rating_seas"]] \
            .rename(columns={"rating_seas": team}) \
            .reset_index(drop=True)
        
        return elo
    
    def get_elo_rating(season: int, home: str, away: str) -> dict:
        with open("./data/mapping/encoder.json") as file:
            encoder = json.load(file)
        
        df = pd.read_parquet("./data/featured/plays.parquet")[["season", "team", "rating_seas"]]
        
        plays = df.query(f"season == {season}")
        
        elo_h, elo_a = pd.DataFrame(), pd.DataFrame()
        
        home = home if home else "None"
        away = away if away else "None"
        
        if home != "None":
            elo_h = query_seas_elo(home, plays, encoder)
        
        if away != "None":
            elo_a = query_seas_elo(away, plays, encoder)
        
        elo = pd.concat([elo_h, elo_a], axis=1) \
            .ffill() \
            .fillna(-1) \
            .to_dict()
        
        return elo
    
    st_subtitle_centre("Elo Rating")
    
    response = get_elo_rating(seas, home, away)
    
    elo = pd.DataFrame().from_dict(response)
    elo.index = elo.index.astype(int)
    
    colour = [["#4E79A7"], ["#4E79A7", "#E15759"]][elo.shape[1] == 2]
    
    st.line_chart(
        data=elo,
        x_label="#. of Games",
        y_label="Elo Rating",
        color=colour,
        use_container_width=True,
    )


def st_probability_matrix(home: str, away: str) -> None:
    def get_probability_matrix(home: str, away: str, max_goals: int=6) -> dict:
        glm = mlflow.statsmodels.load_model("models:/probability_matrix@in_use")
        
        with open("./data/mapping/encoder.json") as file:
            encoder = json.load(file)
        
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
    
    if home and away:
        st_subtitle_centre("Goals Probability Matrix")
        
        data = {"home": home, "away": away}
        
        try:
            response = get_probability_matrix(**data)
            
            if response:
                prob_matrix = pd.DataFrame() \
                    .from_dict(response) \
                    .mul(100)
                
                prob_matrix.index.name = "H\A"
                
                prob_matrix = prob_matrix.style. \
                    text_gradient(cmap="coolwarm", vmin=0, vmax=10) \
                    .format("{:.1f}%")
                
                st.dataframe(prob_matrix, use_container_width=True)
            
            else:
                st_message_box("To view the matrix, first train a model in MLOps tab.", "info")
        
        except:
            st_message_box("To view the matrix, first train a latest model in MLOps tab.", "info")


def st_handicap_prediction(home: str, away: str) -> None:
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
    
    def get_handicap_results(home: str, away: str, time_frame: str, odds_home: float, odds_draw: float, odds_away: float) -> dict:
        
        clf_hc = mlflow.h2o.load_model("models:/handicap_prediction@in_use")
        clf_bd = mlflow.h2o.load_model("models:/bet_decision@in_use")
        
        with open("./data/mapping/encoder.json") as file:
            encoder = json.load(file)
        
        col = [
            "home", "away",
            "rate_h2h_win", "rate_h2h_lose", "knwl_h2h",
            "rank_net", "scores_net",
            "rate_seas_win_net", "rate_seas_lose_net",
            "rating_seas_net", "rating_hist_net",
        ]
        df = pd.read_parquet("./data/predict/j1_predict.parquet")[col]
        
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
    
    def show_decision_img(decision: str, msg: str) -> None:
        with st.columns(3)[1]:
            img_src = f"./frontend/static/imgs/predict/{decision}.png"
            
            st.image(img_src, msg, use_column_width=True)
    
    TIME_MT = {"Before 17:59": "noon", "On or after 18:00": "night"}
    RESULT_MT = {"A": "away", "H": "home"}
    
    if home and away:
        if home != away:
            st_subtitle_centre("Match Information")
            
            with st.form("handicap_prediction", border=False):
                div_h, div_d, div_a = st.columns(3)
                odds_h = div_h.number_input("Home Odds", min_value=1., step=.1)
                odds_d = div_d.number_input("Draw Odds", min_value=1., step=.1)
                odds_a = div_a.number_input("Away Odds", min_value=1., step=.1)
                
                event_time = st.selectbox("Event Time", TIME_MT, index=None)
                time_frame = TIME_MT[event_time] if event_time else None
                
                submitted = st.form_submit_button("Predict")
                
                if submitted:
                    if time_frame:
                        data = {
                            "home": home,
                            "away": away,
                            "odds_home": odds_h,
                            "odds_draw": odds_d,
                            "odds_away": odds_a,
                            "time_frame": time_frame,
                        }
                        response = get_handicap_results(**data)
                        
                        if response:
                            y_hat = response
                            
                            if y_hat["decision"]:
                                decision = RESULT_MT[y_hat["predict"]]
                                caption = "For {:.1f}% of chance {} is gonna win" \
                                    .format(y_hat["probability"]*100, decision)
                            
                            else:
                                decision = "no_action"
                                caption = "No recommended to bet"
                            
                            show_decision_img(decision, caption)
                            
                            st.text_area("", "Disclaimer:\nThe prediction, made using machine learning, are hypothetical in nature and should not be taken as wagering advice. Any betting decisions made based on these recommendations are at users' own risk.")
                            
                            if odds_h == odds_d == odds_a:
                                st_message_box("Odds appear to be the same. Customise them with your favourite dealer before making prediction.", "info")
                        
                        else:
                            st_message_box("To make prediction, first train a model in MLOps tab.", "info")
                    
                    else:
                        st_message_box("Input appears to be missing.", "warning")
        
        else:
            st_message_box("Home and Away team cannot be the same.", "error")
    
    else:
        st_message_box("Select both Home and Away team to continue.", "info")


def prediction_menu() -> None:
    st.header(":rainbow[Asian Handicap Prediction]")
    st.button("Update J1 data", disabled=True, help=MSG_BTN_DISABLE)
    st_row_spacing(3)
    
    home, away = st_team_selection()
    st_row_spacing(2)
    
    if home or away:
        tab_stat, tab_pred = st.tabs(["📊 Statistics", "🔮 Prediction"])
        
        with tab_stat:
            st_recent_games(home, away)
            st_row_spacing(2)
            
            st_season_summary(home, away)
            st_row_spacing(2)
            
            div_left, div_right = st.columns(2)
            with div_left:
                st_elo_rating(home, away)
            with div_right:
                st_probability_matrix(home, away)
        
        with tab_pred:
            st_handicap_prediction(home, away)
    
    st_current_date_time()
