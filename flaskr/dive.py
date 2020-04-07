# Please see LICENSE.md
import pandas;
from flask import (
    Blueprint, render_template
)

from . import plots;
from ..deco import DiveProfile, Gas;

bp = Blueprint('dive', __name__, url_prefix='/dive')


@bp.route('/show')
def show():
    dp = DiveProfile.DiveProfile(gf_low = 35, gf_high = 70);
    dp.add_gas( Gas.Nitrox(50) );
    dp.append_section(20, 43, Gas.Trimix(21, 35));
    dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
    dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
    dp.add_stops_to_surface();
    dp.append_section(0, 30);
    dp.interpolate_points();

    # flash('Hello, world!');
    # flash('Wave!');

    dsdf = pandas.DataFrame([ [ k, v ] for k, v in dp.dive_summary().items() ]);
    return render_template('dive/show.html',
                           dive = dp,
                           summary_table = dsdf.to_html(classes="smalltable", header="true"),
                           dive_profile_plot_json = plots.show_diveprofile(dp),
                           heatmap_plot_json = plots.show_heatmap(dp),
                           fulldata_table = dp.dataframe().to_html(classes = "bigtable", header = "true"),
                           );

