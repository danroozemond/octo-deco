"""
UI-related methods here
"""
import pandas as pd;

# TODO: FIX THIS (now logic is in ui-streamlit.py)

def plot_profile(st, diveprofile):
    # Args: streamlit, diveprofile
    rows = [ (p.time, p.depth) for p in diveprofile.points() ];
    df = pd.DataFrame( rows );
    chart = st.line_chart( df );

