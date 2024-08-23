import os

import requests
import streamlit as st

from utils import st_subtitle_centre


ENDPOINT = os.getenv("ENDPOINT")
ROUTE = f"{ENDPOINT}/api/v1/recent_games?team={{}}"


def get_results(team: str) -> str:
    response = requests.get(ROUTE.format(team))
    
    results = response.json()["response"]
    
    return results


def show_results(team: str, results: str) -> None:
    st.caption(team)
    
    st_subtitle_centre(results, "font-size: 30px;")


def st_recent_games(home: str, away: str) -> None:
    st_subtitle_centre("Recent 5 Games (Left for Most Recent)")
    
    div_home, _, div_away = st.columns((1, .5, 1))
    
    if home:
        with div_home:
            results = get_results(home)
            show_results(home, results)
    
    if away:
        with div_away:
            results = get_results(away)
            show_results(away, results)
