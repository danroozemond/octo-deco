# Please see LICENSE.md
import sys;
import time;

import pandas;
from flask import (
    Blueprint, render_template, Response, flash, redirect, url_for, request, abort, jsonify
)

from octodeco.deco import CreateDive;
from . import db_dive;
from . import plots;
from . import user;
from .app import cache;

bp = Blueprint('dive', __name__, url_prefix='/dive')


@bp.before_request
def load_user_details():
    user.get_user_details();


#
# Getting info
#
def get_gf_args_from_request():
    gflow = request.args.get('gflow', request.form.get('gflow', 101, type=int), type=int);
    gfhigh = request.args.get('gfhigh', request.form.get('gfhigh', 101, type=int), type=int);
    return gflow, gfhigh;


# Using this pattern as it enables invalidation of dive cache as a whole
class CachedDiveProfile:
    def __init__(self, dive_id):
        self.dive_id = dive_id;
        self.lastupdate = time.monotonic();

    def __repr__(self):
        return 'CDP-{}-{}'.format(self.dive_id, self.lastupdate);

    @cache.memoize()
    def profile_base(self):
        print('Actually getting it from DB / updating GF\'s for {} [base]'.format(self));
        dp = db_dive.get_one_dive(self.dive_id);
        if dp is None:
            return None;
        return dp;

    @cache.memoize()
    def profile_gf(self, gflow, gfhigh):
        print('Actually getting it from DB / updating GF\'s for {} {}/{}'.format(self, gflow, gfhigh));
        dp = self.profile_base();
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
    def plot_profile(self, gflow, gfhigh):
        dp = self.profile_gf(gflow, gfhigh);
        try:
            jp = plots.show_diveprofile(dp);
        except TypeError:
            jp = {};
        return jsonify(jp);

    @cache.memoize()
    def plot_heatmap(self, gflow, gfhigh):
        dp = self.profile_gf(gflow, gfhigh);
        try:
            jp = plots.show_heatmap(dp);
        except TypeError:
            jp = {};
        return jsonify(jp);

    @cache.memoize()
    def summary_table(self, gflow, gfhigh):
        dp = self.profile_gf(gflow, gfhigh);
        dsdf = pandas.DataFrame([ [ k, v ] for k, v in dp.dive_summary().items() ]);
        dsdf_table = dsdf.to_html(classes="smalltable", header="true");
        return dsdf_table;

    @cache.memoize()
    def full_table(self, gflow, gfhigh):
        dp = self.profile_gf(gflow, gfhigh);
        fulldata_table = dp.dataframe().to_html(classes = "bigtable", header = "true");
        return fulldata_table;


@cache.memoize()
def get_cached_dive(dive_id: int):
    cdp = CachedDiveProfile(dive_id);
    if cdp is None:
        abort(405);
    if not db_dive.is_display_allowed(cdp.profile_base()):
        abort(403);
    return cdp;


def _invalidate_cached_dive(dive_id: int):
    cache.delete_memoized(get_cached_dive, dive_id);


def get_diveprofile_for_display(dive_id: int):
    gflow, gfhigh = get_gf_args_from_request();
    return get_cached_dive(dive_id).profile_gf(gflow, gfhigh);


#
# Showing the dive: separate elements
#
@bp.route('/show/<int:dive_id>/plot/profile', methods = ['GET'])
def show_elt_plot_profile(dive_id):
    cdp = get_cached_dive(dive_id);
    gflow, gfhigh = get_gf_args_from_request();
    return cdp.plot_profile(gflow, gfhigh);


@bp.route('/show/<int:dive_id>/plot/heatmap', methods = ['GET'])
def show_elt_plot_heatmap(dive_id):
    cdp = get_cached_dive(dive_id);
    gflow, gfhigh = get_gf_args_from_request();
    return cdp.plot_heatmap(gflow, gfhigh);


@bp.route('/show/<int:dive_id>/summary', methods = ['GET'])
def show_elt_summary_table(dive_id):
    cdp = get_cached_dive(dive_id);
    gflow, gfhigh = get_gf_args_from_request();
    return cdp.summary_table(gflow, gfhigh);


@bp.route('/show/<int:dive_id>/full', methods = ['GET'])
def show_elt_full_table(dive_id):
    cdp = get_cached_dive(dive_id);
    gflow, gfhigh = get_gf_args_from_request();
    return cdp.full_table(gflow, gfhigh);


#
# Showing a dive: none, any, get, overview page
#
@bp.route('/show/none')
def show_none():
    return render_template('dive/show_none.html');


@bp.route('/show/get')
def show_get():
    dive_id = request.args.get("dive_id", 0, type=int);
    return redirect(url_for('dive.show', dive_id=dive_id));


@bp.route('/show/<int:dive_id>', methods = ['GET'])
def show(dive_id):
    dp = get_diveprofile_for_display(dive_id);
    if dp is None:
        flash('Dive not found [%i]' % dive_id)
        return redirect(url_for('dive.show_any'));

    alldives = db_dive.get_all_dives();

    return render_template('dive/show.html',
                           dive = dp,
                           alldives = alldives,
                           modify_allowed = db_dive.is_modify_allowed(dp)
                           );


@bp.route('/show/any', methods = [ 'GET'])
def show_any():
    dive_id = db_dive.get_any_dive_id();
    if dive_id is None:
        return redirect(url_for('dive.show_none'));
    else:
        return redirect(url_for('dive.show', dive_id = dive_id))


#
# Downloading CSV
#
@bp.route('/csv/<int:dive_id>')
def csv(dive_id):
    dp = get_diveprofile_for_display(dive_id);
    if dp is None:
        abort(405);
    r = Response(dp.dataframe().to_csv(),
                 mimetype = "text/csv",
                 headers = { "Content-disposition": "attachment; filename=dive_%i.csv" % dive_id }
                 );
    return r;


#
# Update (GF), delete, modify
#
@bp.route('/update/<int:dive_id>', methods = [ 'POST' ])
def update(dive_id):
    action = request.form.get('action');
    gflow, gfhigh = get_gf_args_from_request();
    dp = get_diveprofile_for_display(dive_id);
    if dp is None:
        abort(405);
    if action == 'Update Stops':
        olddecotime = dp.decotime();
        dp.set_gf(gflow, gfhigh);
        dp.update_stops();
        flash('Recomputed stops (deco time: %i -> %i mins)' % (round(olddecotime), round(dp.decotime())));
        db_dive.store_dive(dp);
        _invalidate_cached_dive(dive_id);
        return redirect(url_for('dive.show', dive_id=dive_id));
    else:
        abort(405);


@bp.route('/delete/<int:dive_id>', methods = [ 'GET', 'DELETE' ])
def delete(dive_id):
    aff = db_dive.delete_dive(dive_id);
    if aff == 0:
        abort(405);
    flash('Dive %i is now history' % dive_id);
    _invalidate_cached_dive(dive_id);
    return redirect(url_for('dive.show_any'));


@bp.route('/modify/<int:dive_id>', methods = [ 'POST' ])
def modify(dive_id):
    if request.form.get('action_update', '') != '':
        # Some input sanitation
        ipt_surface_section = min(120, request.form.get('ipt_surface_section', 0, type=int));
        ipt_description = request.form.get('ipt_description')[:100];
        ipt_public = ( request.form.get('ipt_public', 'off').lower() == 'on')
        dp = get_diveprofile_for_display(dive_id);
        dp.remove_surface_at_end();
        if ipt_surface_section > 0:
            flash("Added {} mins surface section".format(ipt_surface_section));
            dp.append_section(0, ipt_surface_section);
        dp.interpolate_points();
        if ipt_description != dp.description():
            flash('Modified description');
            if ipt_description.strip() != '':
                dp.custom_desc = ipt_description;
            else:
                dp.custom_desc = None;
        if ipt_public != dp.is_public:
            flash('Made dive {}'.format( 'public' if ipt_public else 'private'));
            dp.is_public = ipt_public;
        db_dive.store_dive(dp);
        _invalidate_cached_dive(dive_id);
        return redirect(url_for('dive.show', dive_id=dive_id));
    else:
        abort(405);


#
# New (show the page, new from spec, new demo, new from
#
@bp.route('/new', methods = [ 'GET' ])
def new_show():
    return render_template('dive/new.html');


@bp.route('/new', methods = [ 'POST' ])
def new_do():
    dtgs = [ ( request.form.get('depth[%i]' % i, None),
               request.form.get('time[%i]' % i, None),
               request.form.get('gas[%i]' % i, None) )
             for i in range(11) ];
    extragas = request.form.get('deco_gas', '');
    result = CreateDive.create_dive_by_depth_time_gas( dtgs, extragas );
    if result is None:
        # Input sanitation takes place properly in JavaScript. So if something did not work
        # out here, we're not too worried about being nice about it.
        abort(405);
    # Store, return result.
    db_dive.store_dive(result);
    return redirect(url_for('dive.show', dive_id=result.dive_id));


@bp.route('/new/demo', methods = [ 'POST' ])
def new_demo():
    dp = CreateDive.create_demo_dive();
    db_dive.store_dive_new(dp);
    dive_id = dp.dive_id;
    flash('Generated demo dive [%i]' % dive_id);
    return redirect(url_for('dive.show', dive_id = dive_id))


def new_csv( create_csv_func ):
    # Get the object
    if 'ipt_csv' not in request.files:
        flash('No file provided');
        return redirect(url_for('dive.new_show'));
    file = request.files['ipt_csv'];
    # Read line by line
    lines = [];
    sizeseen = 0;
    for line in file:
        lines.append(line.decode('utf-8'));
        sizeseen += sys.getsizeof(line);
        if sizeseen > 5e9:
            flash('File too big');
            return redirect(url_for('dive.new_show'));
    # Create the diveprofile object
    try:
        dp = create_csv_func( lines );
    except CreateDive.ParseError as err:
        flash( 'Error parsing CSV: %s' % err.args );
        return redirect(url_for('dive.new_show'));
    # Store the dive
    db_dive.store_dive_new(dp);
    dive_id = dp.dive_id;
    flash('Import successful - %s' % dp.description());
    # Done.
    return redirect(url_for('dive.show', dive_id = dive_id))


@bp.route('/new/sw_csv', methods = [ 'POST' ])
def new_shearwater_csv():
    return new_csv( CreateDive.create_from_shearwater_csv );


@bp.route('/new/od_csv', methods = [ 'POST' ])
def new_octodeco_csv():
    return new_csv( CreateDive.create_from_octodeco_csv );
