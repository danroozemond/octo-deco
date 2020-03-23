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
dp.append_section(40, 35, gas = Gas.Trimix(21,35));
dp.append_section(21,1);
dp.append_gas_switch(gas = Gas.Nitrox(50), duration = 1.0)
dp.append_section(18, 5);
dp.append_section(15, 5);
dp.append_section(12, 5);
dp.append_section(9, 10);
dp.append_section(6, 15);
dp.append_section(3, 30);
dp.append_surfacing();
dp.append_section(0, 30);
dp.interpolate_points();
dp.update_deco_info();
UI.display_dive(st, dp);
