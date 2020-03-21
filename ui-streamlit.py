import time, math, numpy as np, pandas as pd;
import streamlit as st;

from DiveProfile import DiveProfile;
import UI;

#Run as: streamlit run abc.py

def _max_width_():
    max_width_str = f"max-width: 1500px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )
_max_width_();

st.sidebar.text("Hello, sidebar!");

dp = DiveProfile();
dp.append_section(40,25);
dp.append_section(30,10);
dp.append_surfacing();

UI.display_dive( st, dp );
