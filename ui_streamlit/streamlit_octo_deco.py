# Please see LICENSE.md
import streamlit as st;

from deco import DiveProfile;
from deco import Gas;
from deco import UI;


# Run as: streamlit run abc.py

def go():
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
    #@st.cache(allow_output_mutation=True)
    def do_the_dive(gf_low, gf_high):
        dp = DiveProfile.DiveProfile( gf_low = gf_low, gf_high = gf_high );
        dp.add_gas( Gas.Air() );
        dp.add_gas( Gas.Nitrox(50));
        dp.append_section(10, 2, gas = Gas.Trimix(21, 35));
        dp.append_section(20, 35, gas = Gas.Trimix(21, 35));
        dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
        dp.append_section(40, 33, Gas.Trimix(21, 35));
        dp.add_stops_to_surface();
        dp.append_section(0, 30);
        dp.interpolate_points();
        # print('->', dp.dive_summary());
        # The fact that we have no session state breaks things here...
        return dp;

    # Sidebar
    st.sidebar.markdown("** Hello, world :) **");
    new_gf_low  = st.sidebar.slider('GF low',  10, 100, 35,  5 );
    new_gf_high = st.sidebar.slider('GF high', 10, 100, 70, 5 );
    # do_change_stops = st.sidebar.button('Update profile');
    ddp = do_the_dive(new_gf_low, new_gf_high);

    # st.sidebar.markdown("** Upload file :) **");
    # uploaded_file = st.sidebar.file_uploader("Upload Shearwater dive CSV", type="csv") ## TODO FINISH THIS ##
    # print(uploaded_file);

    # Actual contents
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
