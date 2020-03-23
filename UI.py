"""
UI-related methods here
"""
import numpy;
import plotly.graph_objects as go
import plotly.subplots as sp


# See https://plot.ly/python/multiple-axes/ for some documentation


def _plotly_diveprofile(st, diveprofile):
    df = diveprofile.dataframe();
    #
    # Later, for deco info, see filled lines here: https://plot.ly/python/line-charts/
    #
    st.markdown("""
                Dive profile
                ============
                """);
    fig = sp.make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace( go.Scatter( x=df["time"], y=df["depth"], name='Depth',
                               line={'color': 'rgb(30,7,143)', 'width': 3} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["ceiling"], name='Ceiling',
                               line={'color': 'rgb(251,165,56)', 'dash': 'dot', 'width': 2} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["GF99"], name='GF99',
                               line={'color': 'rgb(255,255,0)', 'width': 3} ),
                   secondary_y = True );
    fig.add_trace( go.Scatter( x=df["time"], y=100*df["ppO2"], name='ppO2',
                               line={'color': 'rgb(176,42,143)', 'dash': 'dot', 'width': 1} ),
                   secondary_y = True );
    fig.update_yaxes(secondary_y = False, autorange = "reversed" );
    fig.update_yaxes(secondary_y = True,  showgrid = False, range=[-1,140], tick0=0, dtick=20);
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
