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
# allow_output_mutation because I'm too lazy to figure out why warning
@st.cache(allow_output_mutation=True)
def do_the_dive():
    dp = DiveProfile();
    dp.append_section(40, 35, gas = Gas.Trimix(21,35));
    dp.append_surfacing();
    dp.add_stops();
    dp.append_section(0, 30);
    dp.interpolate_points();
    return dp;


ddp = do_the_dive();

UI.st_header(st, 'Dive profile');
UI.st_plotly_diveprofile(st, ddp);

UI.st_header(st, 'Summary');
UI.st_dive_summary(st, ddp);

UI.st_header(st, 'Heatmap');
show_heatmap = st.checkbox('Display heatmap');
if show_heatmap:
    UI.st_plotly_tissue_heatmap( st, ddp );

UI.st_header(st, 'Full dive data');
show_data = st.checkbox('Display full dive data');
if show_data:
    UI.st_data(st, ddp);

