import streamlit as st

from modules.pipeline import st_pipeline
from modules.prediction import st_handicap_prediction, st_probability_matrix
from modules.query import (
    st_elo_rating, st_recent_games,
    st_season_summary, st_team_selection,
)
from utils import st_current_date_time, st_row_spacing


def prediction_menu() -> None:
    st.header(":rainbow[Asian Handicap Prediction]")
    st_pipeline()
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
