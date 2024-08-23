import os

import pandas as pd
import requests
import streamlit as st

from utils import st_subtitle_centre


VERSION_MT = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🤡", 5: "💩"}

ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/model_evaluation?versions={{}}"

WARN_CURR_INPUT = "Models trained with latest records are not evaluable."
WARN_MISS_INPUT = "Evaluating models appears to be missing."
WARN_OVER_INPUT = "At most 5 models to be evaluated."


def st_evaluation(expt: str, model_vers: list, model_seas: list) -> str | dict:
    msg = None
    
    n_ids = len(model_vers)
    
    if expt == "handicap_prediction":
        st_subtitle_centre("Model Evaluation")
        
        if st.button("Evaluate", use_container_width=True):
            if n_ids != 0:
                if n_ids <= 5 and "Latest" not in model_seas:
                    vers = ",".join(model_vers)
                    response = requests.get(ROUTE.format(vers))
                    
                    msg = response.json()["response"]
                
                elif "Latest" in model_seas:
                    msg = WARN_CURR_INPUT, "warning"
                
                else:
                    msg = WARN_OVER_INPUT, "warning"
            
            else:
                msg = WARN_MISS_INPUT, "warning"
    
    return msg


def evaluation_message(msg: dict) -> None:
    df = pd.DataFrame().from_dict(msg) \
        .sort_values(by="F1 Score", ascending=False) \
        .reset_index(drop=True)
    
    st_subtitle_centre("F1 Scores on Current Season")
    
    st.bar_chart(df, x="Version", y="F1 Score", horizontal=True)
    
    st_subtitle_centre("Classification Reports")
    
    for idx, rw in df.iterrows():
        rnk = VERSION_MT[idx+1]
        title = f"Model [{rw['Version']}]: Report Details"
        
        with st.expander(title, expanded=not idx, icon=rnk):
            with st.columns((1, 9))[1]:
                report = f"Avg. F1-Scores: {rw['F1 Score']}\n\n" + rw["report"]
                st.text(report)
