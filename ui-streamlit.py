import time, math, numpy as np, pandas as pd;
import streamlit as st;
import plotly.express as px;
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

##
## Create the dive
##

dp = DiveProfile();
dp.append_section(40,25);
dp.append_section(30,10);
dp.append_surfacing();

##
## Displaying it
##
df = dp.dataframe();
st.markdown("""
            Dive profile
            ============
            """);
fig = px.line( df, x="time", y="depth");
fig.update_yaxes(autorange="reversed");
st.plotly_chart( fig, use_container_width = True );

st.markdown("""
            Data
            ====
            """);
st.dataframe(df);

# st.button("Re-plot");
