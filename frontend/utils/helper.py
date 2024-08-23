import os
from datetime import datetime

import pyfiglet
import streamlit as st


def console_message(txt: str) -> None:
    if os.getenv("CONSOLE_PRINT", '1') == '1':
        os.environ["CONSOLE_PRINT"] = '0'
        
        console_msg = pyfiglet.figlet_format(txt, font="small")
        
        print(console_msg)


def st_current_date_time() -> None:
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    st.markdown(
        f"""
        <p style="text-align: right; font-size: 12px;">
          As of <i>{date_time}</i>
        </p>
        """,
        unsafe_allow_html=True,
    )


def st_message_box(msg: str, type_: str) -> None:
    if type_ == "info":
        st.info(msg, icon=f":material/{type_}:")
    
    elif type_ == "warning":
        st.warning(msg, icon=f":material/{type_}:")
    
    elif type_ == "error":
        st.error(msg, icon=f":material/{type_}:")
    
    elif type_ == "success":
        st.success(msg, icon=f":material/check_circle:")


def st_row_spacing(n_row: int) -> None:
    for _ in range(n_row):
        st.write("")


def st_subtitle_centre(msg: str, add_style: str="") -> None:
    st.markdown(
        f"""
        <p style="text-align:center; color:grey; {add_style}">
          {msg}
        </p>
        """,
        unsafe_allow_html=True,
    )
