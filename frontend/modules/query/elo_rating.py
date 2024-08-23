import os
from datetime import date

import pandas as pd
import requests
import streamlit as st

from utils import st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/elo_rating?season={{}}&home={{}}&away={{}}"


def st_elo_rating(home: str, away: str, seas: int=date.today().year) -> None:
    st_subtitle_centre("Elo Rating")
    
    response = requests.get(ROUTE.format(seas, home, away))
    
    elo = pd.DataFrame().from_dict(response.json()["response"])
    elo.index = elo.index.astype(int)
    
    colour = [["#4E79A7"], ["#4E79A7", "#E15759"]][elo.shape[1] == 2]
    
    st.line_chart(
        data=elo,
        x_label="#. of Games",
        y_label="Elo Rating",
        color=colour,
        use_container_width=True,
    )
