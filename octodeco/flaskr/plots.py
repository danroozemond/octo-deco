# Please see LICENSE.md
import json;
import math;

import numpy;
import plotly;
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp


def show_diveprofile(diveprofile):
    df = diveprofile.dataframe();
    fig = sp.make_subplots(specs = [ [ {"secondary_y": True} ] ])
    # First stop: a bit complicated code for adding the shaded area
    fs_xs = list(df[ "time" ]);
    fs_ys1 = list(df[ "FirstStop" ]);
    fs_ys2 = [ 0 for y in fs_ys1 ];
    comp_x = fs_xs + [ fs_xs[ -1 ], fs_xs[ -1 ] ] + fs_xs[ ::-1 ];
    comp_y = fs_ys2 + [ 0, fs_ys1[ -1 ] ] + fs_ys1[ ::-1 ];
    stopinfo = list(df[ "Stops"]);
    stopinfo = stopinfo + ['',''] + stopinfo[ ::-1 ];
    fig.add_trace(go.Scatter(
        x = comp_x,
        y = comp_y,
        fill = 'toself',
        fillcolor = 'rgba(255,0,0,0.2)',
        line_color = 'rgba(255,0,0,0)',
        customdata = stopinfo,
        hoveron = 'points+fills',
        hovertemplate = 'Stops at %{x:.1f}mins: %{customdata}<extra></extra>',
        showlegend = True,
        name = 'Stops',
    ))
    # ppO2
    fig.add_trace(go.Scatter(x = df[ "time" ], y = 100 * df[ "ppO2" ], name = 'ppO2',
                             hovertemplate = 'ppO2: %{customdata:.2f} @ %{x:.1f}mins<extra></extra>',
                             customdata = df[ "ppO2" ],
                             line = {'color': 'rgb(176,42,143)', 'dash': 'dot', 'width': 1},
                             visible = "legendonly"),
                  secondary_y = True);
    # TTS (scaled to make visible, using customdata)
    fig.add_trace(go.Scatter(x = df[ "time" ], y = 2*df[ "TTS" ], name = 'TTS',
                             hovertemplate = 'TTS: %{customdata:.1f}mins @ %{x:.1f}mins<extra></extra>',
                             customdata = df[ "TTS" ],
                             line = {'color': 'rgb(44,160,174)', 'width': 2},
                             visible = "legendonly"),
                  secondary_y = True);
    # Ceil99
    fig.add_trace(go.Scatter(x = df[ "time" ], y = df[ "Ceil99" ], name = 'Ceil GF99',
                             hovertemplate = 'Ceil GF99: %{y:.1f}m @ %{x:.1f}mins<extra></extra>',
                             line = {'color': 'rgb(251,165,56)', 'dash': 'dot', 'width': 2},
                             visible = "legendonly"));
    # Ceil
    fig.add_trace(go.Scatter(x = df[ "time" ], y = df[ "Ceil" ], name = 'Ceil',
                             hovertemplate = 'Ceil: %{y:.1f}m @ %{x:.1f}mins<extra></extra>',
                             line = {'color': 'rgb(251,165,56)', 'dash': 'dot', 'width': 2}));
    # SurfaceGF
    fig.add_trace(go.Scatter(x = df[ "time" ], y = df[ "SurfaceGF" ], name = 'SurfaceGF',
                             hovertemplate = 'SurfaceGF: %{y:.1f} @ %{x:.1f}mins<extra></extra>',
                             line = {'color': 'rgb(251,165,56)', 'width': 3},
                             visible = "legendonly"),
                  secondary_y = True);
    # GF99
    fig.add_trace(go.Scatter(x = df[ "time" ], y = df[ "GF99" ], name = 'GF99',
                             hovertemplate = 'GF99: %{y:.1f} @ %{x:.1f}mins<extra></extra>',
                             line = {'color': 'rgb(255,255,0)', 'width': 3}),
                  secondary_y = True);
    # Depth
    fig.add_trace(go.Scatter(x = df[ "time" ], y = df[ "depth" ], name = 'Depth',
                             hovertemplate = 'Depth: %{y:.1f}m @ %{x:.1f}mins<extra></extra>',
                             line = {'color': 'rgb(30,7,143)', 'width': 3}));
    # Leading tissue -> not that interesting
    # fig.add_trace( go.Scatter( x=df["time"], y=(100/16)*(df["LeadingTissueIndex"]+2), name='Leading tissue',
    #                            line={'color': 'rgb(251,165,56)', 'dash': 'dot', 'width': 1} ),
    #                secondary_y = True );

    #  Set some axes parameters
    fig.update_yaxes(secondary_y = False, autorange = "reversed");
    fig.update_yaxes(secondary_y = True, showgrid = False, range = [ -1, 140 ], tick0 = 0, dtick = 20);
    fig.update_xaxes(title_text = "Time");
    # Draw
    graphjson = json.dumps( fig, cls=plotly.utils.PlotlyJSONEncoder);
    return graphjson;


def show_heatmap(diveprofile):
    # https://plot.ly/python/heatmaps/
    tissue_labels = [ 'T%s' % t for t in diveprofile.deco_model()._constants.N2_HALFTIMES ];
    tissue_labels.reverse();

    values = [ list(p.deco_info[ 'allGF99s' ]) for p in diveprofile.points() ];
    for v in values:
        v.reverse();
    values = numpy.transpose(values);

    times = [ p.time for p in diveprofile.points() ]

    fig = go.Figure(data = go.Heatmap(
        z = values,
        y = tissue_labels,
        x = times,
        hovertemplate = '%{x:.1f}mins, %{y}, GF: %{z:.1f}%<extra></extra>',
        zauto = False, zmin = 0, zmax = 100 ));

    graphjson = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder);
    return graphjson;


def _pg_m_lines(diveprofile, constants):
    def m_line_n2(i, p_amb):
        return constants.N2_A_VALUES[i] + p_amb/constants.N2_B_VALUES[i];
    def m_line_he(i, p_amb):
        return constants.HE_A_VALUES[i] + p_amb/constants.HE_B_VALUES[i];
    if any(map(lambda g:g['fHe'] > 0.0, diveprofile.gases_carried())):
        show_m_lines = [ ('N2', m_line_n2), ('He', m_line_he) ];
    else:
        show_m_lines = [ ('N2', m_line_n2) ];
    return show_m_lines;


def _pg_m_line_gf_ceil(amb_to_gf, i, p_amb, tissue_state):
    gff = amb_to_gf(p_amb) / 100.0;
    a,b = tissue_state._get_coeffs_a_b();
    p_tissue = tissue_state.p_tissue(i);
    # Copied from TissueState[xx].p_ceiling_for_gf_now
    p_ceil = (p_tissue - a[i] * gff) / (gff / b[i] - gff + 1);
    return p_ceil;


def show_pressure_graph(diveprofile):
    fig = sp.make_subplots();
    # The lines
    pts = diveprofile.points();
    # Strip the surface section
    while len(pts) > 2 and pts[-2].depth == 0:
        pts.pop(-1);
    # deco model params
    buhlmann = diveprofile.deco_model();
    con = buhlmann._constants;
    n_tissues = con.N_TISSUES;
    n2halftimes = con.N2_HALFTIMES;
    show_m_lines = _pg_m_lines(diveprofile, con);
    amb_to_gf = pts[-1].deco_info.get('amb_to_gf', None);
    # Get the rest of the reusable info
    colors = px.colors.qualitative.Dark24;
    x = [ p.p_amb for p in pts ];
    max_x = max(x);
    customdata = [ p.time for p in pts ];
    max_y = 0;
    deepest_point = max( pts, key = lambda p: (p.p_amb, p.time) );
    m_line_gf_points = [ pts[-1], deepest_point ];
    # For each tissue ..
    for i in range(n_tissues):
        # The actual line of inert gas pressures
        y = [ p.tissue_state.p_tissue(i) for p in pts ];
        max_y = max(max_y, max(y));
        name = 'T{:.1f}'.format(n2halftimes[i]);
        hovertemplate = '%{customdata:.1f}mins: Ambient:%{x:.1f}, Comptmt:%{y:.1f}<extra>'+name+'</extra>';
        fig.add_trace(go.Scatter(x = x, y = y,
                                 name = name,
                                 mode = 'lines+markers',
                                 legendgroup = name,
                                 customdata = customdata,
                                 hovertemplate = hovertemplate,
                                 line = { 'color' : colors[i] },
                                 marker = { 'symbol': 'circle', 'size' : 4, 'color' : colors[i] },
                                 visible = "legendonly" if i > 0 else True
                                 ));
        # Also add the M-value line(s)
        for t, m_line in show_m_lines:
            xx = [0,1,2,10];
            yy = [ m_line(i, x) for x in xx ];
            fig.add_trace(go.Scatter(x = xx, y = yy,
                                     name = name + '_M_line_' + t,
                                     mode = 'lines',
                                     legendgroup = name,
                                     hovertemplate = '<extra>M-line for '+name+' ('+t+')</extra>',
                                     line = {'color': colors[ i ], 'dash' : 'dot'},
                                     showlegend = False,
                                     visible = "legendonly" if i > 0 else True
                                     ));
        # .. and add the resulting gradient factor line that resulted from the GF's
        if amb_to_gf is not None:
            # x = allowed ambient pressure for y = tissue pressure
            xx = [ _pg_m_line_gf_ceil(amb_to_gf, i, p.p_amb, p.tissue_state) for p in m_line_gf_points ];
            yy = [ p.tissue_state.p_tissue(i) for p in m_line_gf_points ];
            fig.add_trace(go.Scatter(x = xx, y = yy,
                                     name = name + '_M_line_GF',
                                     mode = 'lines',
                                     legendgroup = name,
                                     hovertemplate = '<extra>GF M-line</extra>',
                                     line = {'color': 'red', 'dash' : 'dot'},
                                     showlegend = False,
                                     visible = "legendonly" if i > 0 else True
                                     ));
    # The extra stuff
    max_x = max_x+0.5;
    max_y = max_y+0.5;
    # Ambient = compartment
    fig.add_trace(go.Scatter(x = [0,max(max_x,max_y)],y=[0,max(max_x,max_y)],
                             line = {'color':'grey', 'width':0.5},
                             showlegend=False));
    # Labels etc
    fig.update_yaxes(secondary_y = False, title_text = "Compartment pressure",
                     range = [ 0, max_y ], tick0 = 0, dtick = 1);
    fig.update_xaxes(title_text = "Ambient pressure",
                     range = [ 0, max_x ], tick0 = 0, dtick = 1);
    # Draw
    graphjson = json.dumps( fig, cls=plotly.utils.PlotlyJSONEncoder);
    return graphjson;

