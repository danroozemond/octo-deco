"""
UI-related methods here
"""


def plot_profile(st, diveprofile):
    # Args: streamlit, diveprofile
    chart = st.line_chart()
    new_rows = [ (p.time, p.depth) for p in diveprofile.points() ];
    chart.add_rows(new_rows)
