import streamlit as st;

import Gas
import UI
from DiveProfile import DiveProfile;


# Run as: streamlit run abc.py

# Layout fixes
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
        unsafe_allow_html = True,
    )


# Execute layout fixes
_max_width_();

# Sidebar
st.sidebar.text("Hello, sidebar!");

# Create dive & display
dp = DiveProfile();
dp.append_section(40, 25, gas = Gas.Air());
dp.append_section(30, 10);
dp.append_surfacing();
dp.interpolate_points();

UI.display_dive(st, dp);
