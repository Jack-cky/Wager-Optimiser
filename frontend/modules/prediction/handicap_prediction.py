import os

import requests
import streamlit as st

from utils import st_message_box, st_subtitle_centre


PTH_IMG = os.getenv("PTH_IMG_PREDICT")

TIME_MT = {"Before 17:59": "noon", "On or after 18:00": "night"}
RESULT_MT = {"A": "away", "H": "home"}

ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/handicap_results"

ERROR_SAME_INPUT = "Home and Away team cannot be the same."
INFO_FORGOT_ODDS = """\
Odds appear to be the same. \
Customise them with your favourite dealer before making prediction.
"""
INFO_MISS_MODEL = "To make prediction, first train a model in MLOps tab."
WARN_MISS_INPUT = "Input appears to be missing."
INFO_TEAM_INPUT = "Select both Home and Away team to continue."

DISCLAIMER = """\
Disclaimer:
The prediction, made using machine learning, are hypothetical in \
nature and should not be taken as wagering advice. Any betting \
decisions made based on these recommendations are at users' own risk.
"""


def show_decision_img(decision: str, msg: str) -> None:
    with st.columns(3)[1]:
        img_src = f"{PTH_IMG}/{decision}.png"
        
        st.image(img_src, msg, use_column_width=True)


def st_handicap_prediction(home: str, away: str) -> None:
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
                        response = requests.post(ROUTE, json=data)
                        
                        if response:
                            y_hat = response.json()["response"]
                            
                            if y_hat["decision"]:
                                decision = RESULT_MT[y_hat["predict"]]
                                caption = "For {:.1f}% of chance {} is gonna win" \
                                    .format(y_hat["probability"]*100, decision)
                            
                            else:
                                decision = "no_action"
                                caption = "No recommended to bet"
                            
                            show_decision_img(decision, caption)
                            
                            st.text_area("", DISCLAIMER)
                            
                            if odds_h == odds_d == odds_a:
                                st_message_box(INFO_FORGOT_ODDS, "info")
                        
                        else:
                            st_message_box(INFO_MISS_MODEL, "info")
                    
                    else:
                        st_message_box(WARN_MISS_INPUT, "warning")
        
        else:
            st_message_box(ERROR_SAME_INPUT, "error")
    
    else:
        st_message_box(INFO_TEAM_INPUT, "info")
