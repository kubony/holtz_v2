import streamlit as st

def sync_st_session():
    for k, v in st.session_state.items():
        st.session_state[k] = v
