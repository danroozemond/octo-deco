import pandas;
from flask import (
    Blueprint, flash, render_template
)

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
    dp.interpolate_points();
    dp.append_section(0, 30);

    flash('Hello, world!');
    flash('Wave!');

    dsdf = pandas.DataFrame([ [ k, v ] for k, v in dp.dive_summary().items() ]);

    # Better: https://stackoverflow.com/questions/52644035/how-to-show-a-pandas-dataframe-into-a-existing-flask-html-table
    # Also note: tr:nth-child(even) {
    #     background-color: #dddddd;
    # }

    return render_template('dive/show.html',
                           dive = dp,
                           tables = [ dsdf.to_html(classes='data', header="true")]);

