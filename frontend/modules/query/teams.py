import os
from datetime import date
from pathlib import Path

import requests
import streamlit as st


PTH_IMG = os.getenv("PTH_IMG_TEAM")

ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/teams?season={{}}"


def show_team_img(team: str) -> None:
    imgs = {str(file.stem) for file in Path(f"{PTH_IMG}").glob("*.png")}
    
    if team:
        with st.columns(5)[2]:
            img_name = team if team in imgs else "moto"
            img_src = f"{PTH_IMG}/{img_name}.png"
            
            st.image(img_src, use_column_width=True)


def st_team_selection(seas: int=date.today().year) -> tuple[str, str]:
    response = requests.get(ROUTE.format(seas))
    
    teams = response.json()["response"]
    
    div_home, _, div_away = st.columns((1, .5, 1))
    
    with div_home:
        home = st.selectbox("Home Team", teams, index=None)
        show_team_img(home)
    
    with div_away:
        away = st.selectbox("Away Team", teams, index=None)
        show_team_img(away)
    
    return home, away
