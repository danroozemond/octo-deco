"""
UI-related methods here
"""
import plotly
import plotly.graph_objects as go


# See https://plot.ly/python/multiple-axes/ for some documentation

def display_dive(st, diveprofile):
    # Args: streamlit, diveprofile
    df = diveprofile.dataframe();
    st.markdown("""
                Dive profile
                ============
                """);
    fig = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace( go.Scatter( x=df["time"], y=df["depth"], name='Depth',
                               line={'color':'royalblue'} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["ceiling"], name='Ceiling',
                               line={'color':'green'} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["GF99"], name='GF99',
                               line={'color':'red'} ),
                   secondary_y = True );
    fig.update_yaxes(autorange = "reversed", secondary_y = False);
    fig.update_yaxes(showgrid=False, secondary_y = True);
    fig.update_xaxes(title_text = "Time");
    st.plotly_chart(fig, use_container_width = True);

    st.markdown("""
                Data
                ====
                """);
    st.dataframe(df);
