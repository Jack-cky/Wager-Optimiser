import streamlit as st

from .evaluation import evaluation_message
from utils import st_message_box


def st_system_response(
        msg_train: tuple,
        msg_register: tuple,
        msg_evaluate: tuple | dict,
) -> None:
    if msg_train:
        st_message_box(*msg_train)
    
    if msg_register:
        st_message_box(*msg_register)
    
    if msg_evaluate:
        if isinstance(msg_evaluate, tuple):
            st_message_box(*msg_evaluate)
        
        else:
            evaluation_message(msg_evaluate)
    
    if msg_train or msg_register or msg_evaluate:
        with st.columns(5)[4]:
            st.button("Refresh", use_container_width=True)
