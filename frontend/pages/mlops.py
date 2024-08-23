import streamlit as st

from modules.mlops import (
    st_evaluation, st_experiment_selection, st_leaderboard,
    st_registration, st_system_response, st_training
)
from modules.pipeline import st_pipeline
from utils import st_current_date_time, st_row_spacing


def mlops_menu() -> None:
    st.header(":rainbow[MLOps]")
    st_pipeline()
    st_row_spacing(3)
    
    expt, metric = st_experiment_selection()
    st_row_spacing(2)
    
    if expt:
        run_ids, model_vers, model_seas = st_leaderboard(expt, metric)
        st_row_spacing(2)
        
        div_left, div_middle, div_right = st.columns(3)
        with div_left:
            msg_train = st_training(expt)
        with div_middle:
            msg_register = st_registration(run_ids)
        with div_right:
            msg_evaluate = st_evaluation(expt, model_vers, model_seas)
        st_row_spacing(2)
        
        st_system_response(msg_train, msg_register, msg_evaluate)
    
    st_current_date_time()
