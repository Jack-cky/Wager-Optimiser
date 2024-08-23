import os

import requests
import streamlit as st

from utils import st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/model_registration"

ERROR_FAIL_OUTPUT = "Backend server error."
ERROR_OVER_INPUT = "Select only 1 model to register."
SUCCESS_DONE_OUTPUT = "Model has been registered."
WARN_EXIT_INPUT = "Selected model has already been registered."
WARN_MISS_INPUT = "Registering model appears to be missing."


def st_registration(run_ids: list) -> tuple[str, str]:
    msg = None
    
    n_ids = len(run_ids)
    
    st_subtitle_centre("Model Register")
    
    if st.button("Register", use_container_width=True):
        if n_ids == 1:
            if not next(iter(run_ids.values())):
                run_id = next(iter(run_ids))
                
                response = requests.post(ROUTE, json={"run_id": run_id})
                
                if response:
                    msg = SUCCESS_DONE_OUTPUT, "success"
                
                else:
                    msg = ERROR_FAIL_OUTPUT, "error"
            
            else:
                msg = WARN_EXIT_INPUT, "warning"
        
        elif n_ids == 0:
            msg = WARN_MISS_INPUT, "warning"
        
        else:
            msg = ERROR_OVER_INPUT, "error"
    
    return msg
