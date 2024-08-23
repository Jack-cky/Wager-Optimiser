import os

import pandas as pd
import requests
import streamlit as st

from utils import st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/leaderboard?expt={{}}&metric={{}}"


def st_leaderboard(expt: str, metric: str) -> tuple[dict, list, list]:
    st_subtitle_centre("Leaderboard")
    
    response = requests.get(ROUTE.format(expt, metric))
    
    lb = pd.DataFrame() \
        .from_dict(response.json()["response"]) \
        .sort_values(by=metric.upper())
    
    opts = st.data_editor(
        lb.drop(columns="run_id"),
        column_config={
            "option": st.column_config.CheckboxColumn(
                "Option",
                help="Select model(s) for the following actions.",
                default=False,
            )
        },
        disabled=["In Use"],
        hide_index=True,
        use_container_width=True,
    )
    
    run_ids = lb.loc[opts["option"], ["run_id", "In Use"]] \
        .set_index("run_id") \
        .to_dict()["In Use"]
    
    model_vers = lb.loc[opts["option"], "Version"] \
        .astype(str) \
        .to_list()
    
    model_seas = lb.loc[opts["option"], "Season"] \
        .astype(str) \
        .to_list()
    
    return run_ids, model_vers, model_seas
