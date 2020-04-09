# Please see LICENSE.md
import pandas;
from flask import (
    Blueprint, render_template, Response, flash
)

from . import data;
from . import plots;
from ..deco import DiveProfile, Gas;

bp = Blueprint('dive', __name__, url_prefix='/dive')

@bp.route('/show/', defaults={'id' : 0})
@bp.route('/show/<int:id>')
def show(id):
    dives = data.get_dives();
    dp = None;
    if len(dives) == 0:
        dp = DiveProfile.create_demo_dive();
        data.store_dive_new(dp);
        flash('Generated demo dive [%i]' % dp.dive_id);
    else:
        # TODO FIX
        dp = dives[0];

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
    dp = DiveProfile.DiveProfile(gf_low = 35, gf_high = 70);
    dp.append_section(20, 43, Gas.Trimix(21, 35));
    dp.add_stops_to_surface();
    dp.append_section(0, 30);
    dp.interpolate_points();
    r = Response(dp.dataframe().to_csv(),
                 mimetype = "text/csv",
                 headers = { "Content-disposition" : "attachment; filename=dive_%i.csv" % id }
    );
    return r;
