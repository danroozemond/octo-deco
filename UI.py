"""
UI-related methods here
"""
import pandas as pd;
import plotly.express as px;

def display_dive(st, diveprofile):
    # Args: streamlit, diveprofile
    df = diveprofile.dataframe();
    st.markdown("""
                Dive profile
                ============
                """);
    fig = px.line(df, x = "time", y = "depth");
    fig.update_yaxes(autorange = "reversed");
    st.plotly_chart(fig, use_container_width = True);

    st.markdown("""
                Data
                ====
                """);
    st.dataframe(df);


