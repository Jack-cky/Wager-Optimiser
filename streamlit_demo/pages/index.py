import streamlit as st

from utils import st_row_spacing, st_subtitle_centre


def st_introduction() -> None:
    st_subtitle_centre("Introduction")
    
    msg = """
    Living by the philosophy, "_Small bets for entertainment, big bets to become like [Li Ka-Shing](https://en.wikipedia.org/wiki/Li_Ka-shing)_," sports wagering offers an adrenaline-filled experience. The hook lies in the unpredictable outcome, which keeps the excitement high throughout the match.
    """
    
    st.write(msg)


def st_league() -> None:
    st_subtitle_centre("J1 League")
    
    msg = """
    The [J1 League](https://www.jleague.co/) is the top division in Japan's professional football hierarchy. Established in 1992, it is known for its high-caliber gameplay, fostering both domestic talent and attracting international stars. The league promotes dynamic, fast-paced football and is avidly followed by fans worldwide.
    """
    
    st.write(msg)

def st_methodology() -> None:
    st_subtitle_centre("Methodology")
    
    msg = """
    Embarking on an innovative journey, we aspire to forecast the [Asian Handicap](https://is.hkjc.com/football/info/en/betting/bettypes_hdc.asp) results in the J1 League employing an end-to-end machine learning solution. Leveraging historical results and betting odds data, [AutoML](https://en.wikipedia.org/wiki/Automated_machine_learning) finds the optimal solution for model training and hyperparameter tuning. This is not only an intriguing challenge for machine learning enthusiasts but also has significant potential in becoming the next Li Ka-Shing.
    """
    
    st.write(msg)


def index_menu() -> None:
    st.header(":rainbow[Home]")
    st_row_spacing(3)
    
    st_introduction()
    st_row_spacing(2)
    
    st_league()
    st_row_spacing(2)
    
    st_methodology()
