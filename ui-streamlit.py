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


# Create dive & display
# allow_output_mutation because I'm too lazy to figure out why warning :)
@st.cache(allow_output_mutation=True)
def do_the_dive(gf_low, gf_high):
    dp = DiveProfile( gf_low = new_gf_low, gf_high = new_gf_high)
    dp.add_gas( Gas.Air() );
    dp.add_gas( Gas.Nitrox(50));
    dp.append_section(20, 35, gas = Gas.Trimix(21, 35));
    dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
    dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
    dp.add_stops_to_surface();
    dp.append_section(0, 30);
    dp.interpolate_points();
    return dp;

# Sidebar
st.sidebar.markdown("** Hello, sidebar :) **");
new_gf_low  = st.sidebar.slider('GF low',  10, 100, 35,  5 );
new_gf_high = st.sidebar.slider('GF high', 10, 100, 70, 5 );

ddp = do_the_dive(new_gf_low, new_gf_high);

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

