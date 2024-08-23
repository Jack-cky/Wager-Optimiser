import os

import pandas as pd
import requests
import streamlit as st

from utils import st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/seasonal_summary?home={{}}&away={{}}"


def st_season_summary(home: str, away: str) -> None:
    st_subtitle_centre("Seasonal Summary")
    
    response = requests.get(ROUTE.format(home, away))
    
    smy = pd.DataFrame() \
        .from_dict(response.json()["response"]) \
        .style.format("{:.1f}%", "Win Rate (%)")
    
    st.dataframe(smy, use_container_width=True)
