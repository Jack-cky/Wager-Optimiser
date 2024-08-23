from dotenv import load_dotenv
load_dotenv("config/.env")

import os

import streamlit as st
from streamlit_navigation_bar import st_navbar

from pages import index_menu, mlops_menu, prediction_menu
from utils import console_message


PTH_IMG = os.getenv("PTH_IMG_LOGO")

console_message("Wager Optimisation Frontend Server")

st.set_page_config(
    page_title="Wager Optimisation",
    page_icon="soccer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = [
    "Prediction", "MLOps", "GitHub",
]

logo_path = f"./{PTH_IMG}/logo.svg"

urls = {
    "GitHub": "https://github.com/Jack-cky/Wager-Optimisation",
}

styles = {
    "nav": {
        "background-color": "#C63834",
        "justify-content": "left",
    },
    "img": {
        "padding-right": "14px",
    },
    "span": {
        "color": "white",
        "font-weight": "bold",
        "padding": "14px",
    },
    "active": {
        "background-color": "white",
        "color": "var(--text-color)",
        "font-weight": "bold",
        "padding": "14px",
    },
}

options = {
    "show_menu": True,
    "show_sidebar": False,
}

page = st_navbar(
    pages,
    logo_path=logo_path,
    urls=urls,
    styles=styles,
    options=options,
    selected="Prediction",
)

functions = {
    "Home": index_menu,
    "Prediction": prediction_menu,
    "MLOps": mlops_menu,
}

go_to = functions.get(page)

if go_to:
    go_to()
