# Please see LICENSE.md
import pandas;
from flask import (
    Blueprint, render_template, Response, flash, redirect, url_for, request, abort
)

from . import data;
from . import plots;
from ..deco import DiveProfile;

bp = Blueprint('dive', __name__, url_prefix='/dive')


@bp.route('/show/')
def show_any():
    dive_id = data.get_any_dive_id();
    if dive_id is None:
        dp = DiveProfile.create_demo_dive();
        data.store_dive_new(dp);
        dive_id = dp.dive_id;
        flash('Generated demo dive [%i]' % dive_id);
    return redirect(url_for('dive.show', id = dive_id))


@bp.route('/show/<int:id>')
def show(id):
    dp = data.get_one_dive(id);
    if dp is None:
        return redirect(url_for('dive.show_any'));

    dsdf = pandas.DataFrame([ [ k, v ] for k, v in dp.dive_summary().items() ]);
    return render_template('dive/show.html',
                           dive = dp,
                           summary_table = dsdf.to_html(classes="smalltable", header="true"),
                           dive_profile_plot_json = plots.show_diveprofile(dp),
                           heatmap_plot_json = plots.show_heatmap(dp),
                           fulldata_table = dp.dataframe().to_html(classes = "bigtable", header = "true"),
                           );


@bp.route('/csv/<int:id>')
def csv(id):
    dp = data.get_one_dive(id);
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
    dp = data.get_one_dive(id);
    olddecotime = dp.decotime();
    if dp is None:
        abort(405);
    if action == 'Update Display GF' or action == 'Update Stops':
        gflow = int(request.form.get('gflow', 0));
        gfhigh = int(request.form.get('gfhigh', 0));
        dp.set_gf(gflow, gfhigh);
        if action == 'Update Stops':
            dp.update_stops();
            flash('Recomputed stops (deco time: %i -> %i mins)' % (olddecotime, dp.decotime()));
        data.store_dive(dp);
        return redirect(url_for('dive.show', id=id));
    else:
        abort(405);
