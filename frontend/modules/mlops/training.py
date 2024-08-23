import os
from datetime import date

import requests
import streamlit as st

from utils import st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE_SMY = f"{ENDPOINT}/api/v1/pre_train_summary?expt={{}}&season={{}}"
ROUTE_TRAIN = f"{ENDPOINT}/api/v1/model_training"

BTN_SEAS = "Train a **SEASON** model"
BTN_CURR = "Train a **LATEST** model"

ERROR_FAIL_OUTPUT = "Backend server error."
SUCCESS_DONE_OUTPUT = "Model has been trained."


def pre_train_summary(expt: str, seas: int) -> None:
    response = requests.get(ROUTE_SMY.format(expt, seas))
    
    train_dev_size = response.json()["response"]
    
    st.markdown(
        f"""
        Model will be trained in the following split size:
        - Train: {train_dev_size[0]:,}
        - Dev: {train_dev_size[1]:,}
        """
    )


def train_model(expt: str, seas: int, is_latest: bool) -> tuple[str, str]:
    data = {"expt": expt, "season": seas, "is_latest": is_latest}
    response = requests.post(ROUTE_TRAIN, json=data)
    
    if response:
        msg = SUCCESS_DONE_OUTPUT, "success"
    
    else:
        msg = ERROR_FAIL_OUTPUT, "error"
    
    return msg


def st_training(expt: str, seas_curr: int=date.today().year) -> None:
    msg = None
    
    st_subtitle_centre("Model Training")
    
    with st.expander("Options", icon="🚀"):
        seasons = [seas for seas in range(seas_curr-1, 2012, -1)]
        season = st.selectbox("Select a season", seasons, index=None)
        
        if st.button(BTN_SEAS, disabled=season==None, use_container_width=True):
            msg = train_model(expt, season, False)
        
        if st.button(BTN_CURR, disabled=season!=None, use_container_width=True):
            msg = train_model(expt, seas_curr, True)
        
        if not season:
            season = seas_curr
        
        st.divider()
        st_subtitle_centre("Pre-Traing Summary")
        
        pre_train_summary(expt, season)
    
    return msg
