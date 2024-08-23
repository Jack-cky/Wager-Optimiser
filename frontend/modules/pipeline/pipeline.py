import os

import requests
import streamlit as st


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/pipeline"

ERROR_FAIL_OUTPUT = "✗ Failed: Backend server error."
SUCCESS_DONE_OUTPUT = "✔️ Succeed: Data has been updated."


def st_pipeline() -> None:
    if st.session_state.get("pipeline", False):
        st.session_state.disabled = True
    
    div_left, div_rright = st.columns((1, 4))
    with div_left:
        click = st.button(
            "Update J1 data",
            key="pipeline",
            disabled=st.session_state.get("disabled", False),
        )
    with div_rright:
        if click:
            response = requests.post(ROUTE)
            
            if response:
                msg = SUCCESS_DONE_OUTPUT
            
            else:
                msg = ERROR_FAIL_OUTPUT
            
            st.text(msg)
