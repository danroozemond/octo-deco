# Please see LICENSE.md
import time;

import pandas;
from flask import (
    g, Blueprint, flash, redirect, url_for, request, abort, jsonify, session
)

from . import db_dive, plots, user, db_api_dive;
from .app import cache;


bp = Blueprint('dive', __name__, url_prefix='/dive')


@bp.before_request
def load_user_details():
    user.get_user_details();


#
# Getting info
#
def _get_arg_multikey(args, tp, keys, default):
    r = None;
    try:
        for k in keys:
            r = args.get(k);
            if r is not None and r != '':
                return tp(r);
    except ValueError:
        pass;
    return default;


def get_gf_args_from_request():
    if 'gf_args' not in g:
        # GFs
        args = dict(request.args);
        args.update(request.form);
        gflow = min(200, max(0, _get_arg_multikey(args, int, [ 'ipttxt_gflow', 'gflow'], 101)));
        gfhigh = min(200, max(0, _get_arg_multikey(args, int, [ 'ipttxt_gfhigh', 'gfhigh' ], 101)));
        # Done
        g.gf_args = { 'gflow': gflow, 'gfhigh': gfhigh };
    return g.gf_args;


# Using this pattern as it enables invalidation of dive cache as a whole
class CachedDiveProfile:
    def __init__(self, dive_id):
        self.dive_id = dive_id;
        self.lastupdate = time.monotonic();

    def __repr__(self):
        return 'CDP-{}-{}'.format(self.dive_id, self.lastupdate);

    @cache.memoize()
    def profile_base(self):
        dp = db_api_dive.get_one_dive(self.dive_id);
        if dp is None:
            return None;
        return dp;

    @cache.memoize()
    def profile_args(self, req_args):
        dp = self.profile_base();
        # Gradient factors
        gflow = req_args['gflow'];
        gfhigh = req_args['gfhigh'];
        if dp is None:
            return None;
        if (gflow, gfhigh) == (101, 101):
            gflow, gfhigh = dp.gf_low_display, dp.gf_high_display;
        if (gflow, gfhigh) != (dp.gf_low_display, dp.gf_high_display):
            dp.set_gf(gflow, gfhigh);
        return dp;

    @cache.memoize()
    def user_id(self):
        return self.profile_base().user_id;

    @cache.memoize()
    def plot_profile(self, req_args):
        dp = self.profile_args(req_args);
        try:
            jp = plots.show_diveprofile(dp);
        except TypeError:
            jp = {};
        return jsonify(jp);

    @cache.memoize()
    def plot_heatmap(self, req_args):
        dp = self.profile_args(req_args);
        try:
            jp = plots.show_heatmap(dp);
        except TypeError:
            jp = {};
        return jsonify(jp);

    @cache.memoize()
    def plot_pressure_graph(self, req_args):
        dp = self.profile_args(req_args);
        try:
            jp = plots.show_pressure_graph(dp);
        except TypeError:
            jp = {};
        return jsonify(jp);

    @cache.memoize()
    def summary_table(self, req_args):
        dp = self.profile_args(req_args)
        dsdf = pandas.DataFrame([ [ k, v ] for k, v in dp.dive_summary().items() ]);
        dsdf_table = dsdf.to_html(classes="smalltable", header="true");
        return dsdf_table;

    @cache.memoize()
    def runtime_table(self, req_args):
        dp = self.profile_args(req_args);
        rtt = dp.runtimetable();
        if rtt is None:
            return 'A runtime table is unfortunately not available for this dive.';
        dsdf = pandas.DataFrame(rtt);
        desired_col_seq = [ 'depth', 'time', 'gas', 'gas_usage' ];
        for c in set(desired_col_seq).difference(dsdf.columns):
            dsdf[ c ] = '';
        dsdf = dsdf[ desired_col_seq ].rename(columns = {'gas_usage': 'gas usage'});
        frm = {
            'depth': lambda x: '{:.0f}'.format(x),
            'time': lambda x: '{:.1f}'.format(x) if not pandas.isnull(x) else '',
            'gas': str,
            'gas usage': lambda d: ', '.join([ '{}: {:.0f}L used ({:.0f} bar from {})'.format(gas,inf['liters_used'], inf['bars_used'], inf['cyl_name']) for gas,inf in d.items() ])
        };
        dsdf_table = dsdf.to_html(classes="smalltable", header="true",
                                  formatters=frm, na_rep='');
        return dsdf_table;

    @cache.memoize()
    def gas_consumption_table(self):
        def format_lost_gas_link(slost):
            if slost is None:
                return 'planned';
            else:
                return '<a href="{}?lostgas={}">lost {}</a>'.\
                    format(url_for('dive.new_ephm_lost_gas', dive_id=self.dive_id), slost, slost);
        def format_emergency(dp, dict_emerg):
            tooltip = 'In the event of an emergency ({:.0f}x, {:.0f}mins) at {:.0f}m you need {:.0f}% of the bottom gas {} in your {}'\
                .format(dp._gas_consmp_emerg_factor, dp._gas_consmp_emerg_mins, dp.max_depth(),
                        dict_emerg['perc_emerg'], dict_emerg['bottom_gas'], dict_emerg['cyl_name']);
            text = '{:.0f}%'.format(dict_emerg['perc_emerg']);
            cl = 'gas_{}'.format(dict_emerg['ok']);
            return '<div class="tooltip {}">{}<span class="tooltiptext">{}</span></div>'.format(cl, text, tooltip);
        def format_gas_usage(gas, inf):
            if inf['liters'] == 0.0:
                return '-';
            text1 = '{:.0f}L'.format(inf['liters']);
            text2 = '{:.0f}%'.format(inf['perc']);
            tooltip = '{:.0f}bar of {}'.format(inf['bars'], inf['cyl_name']);
            cl = 'gas_{}'.format(inf['ok']);
            r = '{} [<span class="tooltip {}">{}<span class="tooltiptext">{}</span></span>]'.format(text1, cl, text2, tooltip);
            return r;
        dp = self.profile_base();
        gct = dp.gas_consumption_analysis();
        gct_formatted = {
            format_lost_gas_link(s['lost'])
            :
            { ' deco time': '{:.1f}mins'.format(s[ 'decotime' ]),
              ' emergency': format_emergency(dp, s['emergency']),
              **{str(gas): format_gas_usage(gas, inf)
                 for gas, inf in s[ 'gas_consmp' ].items()}}
            for s in gct };
        dsdf = pandas.DataFrame(gct_formatted);
        dsdf_table = dsdf.to_html(classes="smalltable", na_rep='', escape=False);
        info = 'Computed with bottom: {:.1f}L/min, deco: {:.1f}L/min.'.\
            format(dp._gas_consmp_bottom, dp._gas_consmp_deco);
        warning = ' This does not always fully take max pO2 into account.';
        return dsdf_table + '<br/>'+ info + warning;

    @cache.memoize()
    def full_table(self, req_args):
        dp = self.profile_args(req_args);
        fulldata_table = dp.dataframe().to_html(classes = "bigtable", header = "true");
        return fulldata_table;

    @cache.memoize()
    def gfdeco_table(self, req_args):
        dp = self.profile_args(req_args)
        t0 = time.perf_counter();
        dtt = dp.decotimes_for_gfs();
        t1 = time.perf_counter();
        if dtt is None:
            return 'Such a table is unfortunately not available for this dive.';
        # Format
        url = url_for('dive.show', dive_id=self.dive_id);
        dtt2 = { gflow: {
                gfhigh: (val,
                         '<a href="{}?gflow={:d}&gfhigh={:d}">{:.1f}</a>'.format(url, gflow, gfhigh, val),
                         gflow == dp.gf_low_profile and gfhigh == dp.gf_high_profile)
                for gfhigh, val in r.items() } for gflow, r in dtt.items() };
        minv = min(min([ v for v in r.values() ] for r in dtt.values()));
        maxv = max(max([ v for v in r.values() ] for r in dtt.values()));
        def style_map(v):
            try:
                op = (v[0]-minv)/(maxv-minv);
            except ZeroDivisionError:
                op = 0.5;
            # base color varies between 150,150,150 and 230,230,230
            r = 'background-color:rgba({0},{0},{0},0.35);'.format(150 + round((1-op)*80));
            if v[2]:
                # Matches current GF's.
                r += 'border:2px dashed black';
            return r;
        def format_map(v):
            return v[1];
        df = pandas.DataFrame(dtt2).transpose();
        styled_df = df.style\
            .set_table_attributes('class="dataframe gfdecotable smalltable"')\
            .applymap(style_map)\
            .format(format_map)\
            .render(classes="smalltable");
        html_comp_time = 'Computation time: {:.2f}s.'.format(t1-t0);
        return styled_df + '<br/>' + html_comp_time;


@cache.memoize()
def get_cached_dive(dive_id: int):
    cdp = CachedDiveProfile(dive_id);
    if cdp is None or cdp.profile_base() is None:
        session[ 'last_dive_id' ] = None;
        abort(404);
    if not db_dive.is_display_allowed(cdp.profile_base()):
        session[ 'last_dive_id' ] = None;
        abort(403);
    if not cdp.profile_base().is_ephemeral:
        session[ 'last_dive_id' ] = dive_id;
    return cdp;


def invalidate_cached_dive(dive_id: int):
    cache.delete_memoized(get_cached_dive, dive_id);


def get_diveprofile_for_display(dive_id: int):
    return get_cached_dive(dive_id).profile_args(get_gf_args_from_request());


#
from . import dive_show;
from . import dive_change;
from . import dive_new;
