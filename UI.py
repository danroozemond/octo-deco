"""
UI-related methods here
"""
import numpy;
import pandas;
import plotly.graph_objects as go
import plotly.subplots as sp


# See https://plot.ly/python/multiple-axes/ for some documentation

def st_header(st, text):
    st.markdown("""
                %s
                ============
                """ % text);


def st_plotly_diveprofile(st, diveprofile):
    df = diveprofile.dataframe();
    #
    # Later, for deco info, see filled lines here: https://plot.ly/python/line-charts/
    #
    fig = sp.make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace( go.Scatter( x=df["time"], y=df["depth"], name='Depth',
                               line={'color': 'rgb(30,7,143)', 'width': 3} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["Ceil"], name='Ceil',
                               line={'color': 'rgb(251,165,56)', 'dash': 'dot', 'width': 2} ) );
    fig.add_trace( go.Scatter( x=df["time"], y=df["GF99"], name='GF99',
                               line={'color': 'rgb(255,255,0)', 'width': 3} ),
                   secondary_y = True );
    fig.add_trace( go.Scatter( x=df["time"], y=100*df["ppO2"], name='ppO2',
                               line={'color': 'rgb(176,42,143)', 'dash': 'dot', 'width': 1} ),
                   secondary_y = True );
    # Leading tissue - not that interesting
    # fig.add_trace( go.Scatter( x=df["time"], y=(100/16)*(df["LeadingTissueIndex"]+2), name='Leading tissue',
    #                            line={'color': 'rgb(251,165,56)', 'dash': 'dot', 'width': 1} ),
    #                secondary_y = True );
    # A bit complicated code for adding the shaded area
    fs_xs = list(df["time"]);
    fs_ys1 = df["FirstStop"];
    fs_ys2 = [ 0 for y in fs_ys1 ];
    print(len(fs_xs), len(fs_xs[::-1]), len(fs_ys1), len(fs_ys2));
    fig.add_trace( go.Scatter(
        x = fs_xs + fs_xs[::-1],
        y = fs_ys2 + fs_ys1,
        fill = 'toself',
        fillcolor = 'rgba(255,0,0,0.2)',
        line_color = 'rgba(255,0,0,0)',
        showlegend = True,
        name = '1st stop',
    ))
    #  Set some axes parameters; draw
    fig.update_yaxes(secondary_y = False, autorange = "reversed" );
    fig.update_yaxes(secondary_y = True,  showgrid = False, range=[-1, 140], tick0=0, dtick=20);
    fig.update_xaxes(title_text = "Time");
    st.plotly_chart(fig, use_container_width = True);


def st_plotly_tissue_heatmap( st, diveprofile ):
    st.markdown(
        """
        Displays (scaled) compartment pressure (actually: GF99)
        """);
    # https://plot.ly/python/heatmaps/
    # will need zauto=False, zmin=0, zmax=100
    tissue_labels = [ 'T%s' % t for t in diveprofile.deco_model()._halftimes['N2'] ];
    tissue_labels.reverse();

    values = [ p.deco_info[ 'allGF99s' ] for p in diveprofile.points() ];
    for v in values:
        v.reverse();
    values = numpy.transpose(values);

    times = [ p.time for p in diveprofile.points() ]

    fig = go.Figure(data = go.Heatmap(
        z = values,
        y = tissue_labels,
        x = times,
        zauto = False, zmin = 0, zmax = 100 ));
    st.plotly_chart(fig, use_container_width = True);


def st_data(st, diveprofile):
    st.write(diveprofile.dataframe());


def st_dive_summary(st, diveprofile):
    ds = diveprofile.dive_summary();
    dsdf = pandas.DataFrame( [ [ k, v] for k, v in ds.items() ]);
    st.write(dsdf);
