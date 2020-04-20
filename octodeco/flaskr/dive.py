# Please see LICENSE.md
import pandas;
from flask import (
    Blueprint, render_template, Response, flash, redirect, url_for, request, abort
)
import sys;

from . import db_dive;
from . import plots;
from octodeco.deco import CreateDive;

bp = Blueprint('dive', __name__, url_prefix='/dive')


@bp.route('/show/', methods = [ 'GET'])
def show_any():
    dive_id = db_dive.get_any_dive_id();
    if dive_id is None:
        return new_demo();
    else:
        return redirect(url_for('dive.show', id = dive_id))


@bp.route('/show/<int:id>', methods = ['GET'])
def show(id):
    dp = db_dive.get_one_dive(id);
    if dp is None:
        return redirect(url_for('dive.show_any'));

    alldives = db_dive.get_all_dives();
    dsdf = pandas.DataFrame([ [ k, v ] for k, v in dp.dive_summary().items() ]);
    return render_template('dive/show.html',
                           dive = dp,
                           alldives = alldives,
                           summary_table = dsdf.to_html(classes="smalltable", header="true"),
                           dive_profile_plot_json = plots.show_diveprofile(dp),
                           heatmap_plot_json = plots.show_heatmap(dp),
                           fulldata_table = dp.dataframe().to_html(classes = "bigtable", header = "true"),
                           );


@bp.route('/show/', methods = [ 'POST' ] )
def show_post():
    dive_id = int(request.form.get('dive_id'));
    return redirect(url_for('dive.show', id=dive_id));


@bp.route('/csv/<int:id>')
def csv(id):
    dp = db_dive.get_one_dive(id);
    if dp is None:
        abort(405);
    r = Response(dp.dataframe().to_csv(),
                 mimetype = "text/csv",
                 headers = { "Content-disposition" : "attachment; filename=dive_%i.csv" % id }
    );
    return r;


@bp.route('/update/<int:id>', methods = [ 'POST' ])
def update(id):
    action = request.form.get('action');
    if action is None:
        action = 'Update Display GF';
    dp = db_dive.get_one_dive(id);
    olddecotime = dp.decotime();
    if dp is None:
        abort(405);
    if action == 'Update Display GF' or action == 'Update Stops':
        gflow = int(request.form.get('gflow', 0));
        gfhigh = int(request.form.get('gfhigh', 0));
        dp.set_gf(gflow, gfhigh);
        if action == 'Update Stops':
            dp.update_stops();
            flash('Recomputed stops (deco time: %i -> %i mins)' % (round(olddecotime), round(dp.decotime())));
        db_dive.store_dive(dp);
        return redirect(url_for('dive.show', id=id));
    else:
        abort(405);


@bp.route('/delete/<int:id>', methods = [ 'POST' ])
def delete(id):
    aff = db_dive.delete_dive(id);
    if aff == 0:
        abort(405);
    flash('Dive %i is now history' % id);
    return redirect(url_for('dive.show_any'));


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
    return redirect(url_for('dive.show', id=result.dive_id));


@bp.route('/new/demo', methods = [ 'POST' ])
def new_demo():
    dp = CreateDive.create_demo_dive();
    db_dive.store_dive_new(dp);
    dive_id = dp.dive_id;
    flash('Generated demo dive [%i]' % dive_id);
    return redirect(url_for('dive.show', id = dive_id))


@bp.route('/new/csv', methods = [ 'POST' ])
def new_shearwater_csv():
    CHARSET='utf-8';
    # Get the object
    if 'ipt_csv' not in request.files:
        flash('No file provided');
        return redirect(url_for('dive.new_show'));
    file = request.files['ipt_csv'];
    # Read line by line
    lines = [];
    sizeseen = 0;
    for line in file:
        lines.append(line.decode(CHARSET));
        sizeseen += sys.getsizeof(line);
        if sizeseen > 5e9:
            flash('File too big');
            return redirect(url_for('dive.new_show'));
    # Create the diveprofile object
    try:
        dp = CreateDive.create_from_shearwater_csv( lines );
    except CreateDive.ParseError as err:
        flash( 'Error parsing CSV: %s' % err.args );
        return redirect(url_for('dive.new_show'));
    # Store the dive
    db_dive.store_dive_new(dp);
    dive_id = dp.dive_id;
    flash('Import successful - %s' % dp.description());
    # Done.
    return redirect(url_for('dive.show', id = dive_id))
