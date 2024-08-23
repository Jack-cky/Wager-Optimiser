import os

import pandas as pd
import requests
import streamlit as st

from utils import st_message_box, st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/probability_matrix"

INFO_MISS_MODEL = "To view the matrix, first train a model in MLOps tab."
INFO_UNTRAINED_TEAM = "To view the matrix, first train a latest model in MLOps tab."


def st_probability_matrix(home: str, away: str) -> None:
    if home and away:
        st_subtitle_centre("Goals Probability Matrix")
        
        data = {"home": home, "away": away}
        response = requests.post(ROUTE, json=data)
        
        if response:
            prob_matrix = pd.DataFrame() \
                .from_dict(response.json()["response"]) \
                .mul(100)
            
            prob_matrix.index.name = "H\A"
            
            prob_matrix = prob_matrix.style. \
                text_gradient(cmap="coolwarm", vmin=0, vmax=10) \
                .format("{:.1f}%")
            
            st.dataframe(prob_matrix, use_container_width=True)
        
        elif response.status_code == 404:
            st_message_box(INFO_MISS_MODEL, "info")
        
        elif response.status_code == 422:
            st_message_box(INFO_UNTRAINED_TEAM, "info")
