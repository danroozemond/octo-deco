"""
UI-related methods here
"""
import numpy;
import plotly.graph_objects as go
import plotly.subplots as sp


# See https://plot.ly/python/multiple-axes/ for some documentation


def _plotly_diveprofile(st, diveprofile):
    df = diveprofile.dataframe();
    st.markdown("""
                Dive profile
                ============
                """);
    fig = sp.make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace( go.Scatter( x=df["time"], y=df["depth"], name='Depth',
                               line={'color': 'royalblue'} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["ceiling"], name='Ceiling',
                               line={'color': 'green'} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["GF99"], name='GF99',
                               line={'color': 'red'} ),
                   secondary_y = True );
    fig.update_yaxes(autorange = "reversed", secondary_y = False);
    fig.update_yaxes(showgrid=False, secondary_y = True);
    fig.update_xaxes(title_text = "Time");
    st.plotly_chart(fig, use_container_width = True);


def _plotly_tissue_heatmap( st, diveprofile ):
    st.markdown(
        """
        Heatmap
        =======
        Displays (scaled) compartment pressure (actually: GF99)
        """);
    # https://plot.ly/python/heatmaps/
    # will need zauto=False, zmin=0, zmax=100
    tissue_labels = [ 'T%s' % t for t in diveprofile.deco_model()._halftimes['N2'] ];
    tissue_labels.reverse();
    values = [ p.deco_info['allGF99s'] for p in diveprofile.points() ];
    for v in values:
        v.reverse();
    values = numpy.transpose(values);
    fig = go.Figure(data = go.Heatmap(
        z = values,
        y = tissue_labels,
        zauto = False, zmin = 0, zmax = 100 ));
    st.plotly_chart(fig, use_container_width = True);


def display_dive(st, diveprofile):
    # Args: streamlit, diveprofile
    _plotly_diveprofile( st, diveprofile );

    _plotly_tissue_heatmap( st, diveprofile );

    st.markdown("""
                Data
                ====
                """);
    st.dataframe(diveprofile.dataframe());
