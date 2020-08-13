from . import dive, user;
from . import db_dive;
from .dive import bp;
from flask import (
    redirect, url_for, request, abort, session, render_template, Response
)


#
# Showing the dive: separate elements
#
@bp.route('/show/<int:dive_id>/plot/profile', methods = ['GET'])
def show_elt_plot_profile(dive_id):
    return dive.get_cached_dive(dive_id).plot_profile(dive.get_gf_args_from_request());


@bp.route('/show/<int:dive_id>/plot/heatmap', methods = ['GET'])
def show_elt_plot_heatmap(dive_id):
    return dive.get_cached_dive(dive_id).plot_heatmap(dive.get_gf_args_from_request());


@bp.route('/show/<int:dive_id>/summary', methods = ['GET'])
def show_elt_summary_table(dive_id):
    cdp = dive.get_cached_dive(dive_id);
    reqargs = dive.get_gf_args_from_request();
    r1 = cdp.summary_table(reqargs);
    r2 = cdp.runtime_table(reqargs);
    r3 = cdp.gas_consumption_table();
    return '{}\n<h3>Runtime</h3>\n{}\n<h3>Gas consumption</h3>\n{}\n'.format(r1,r2,r3);


@bp.route('/show/<int:dive_id>/fulldata', methods = ['GET'])
def show_elt_full_table(dive_id):
    return dive.get_cached_dive(dive_id).full_table(dive.get_gf_args_from_request());


@bp.route('/show/<int:dive_id>/gfdecodata', methods = ['GET'])
def show_elt_gfdeco_table(dive_id):
    cdp = dive.get_cached_dive(dive_id);
    if user.get_user_details().is_logged_in():
        return cdp.gfdeco_table(dive.get_gf_args_from_request());
    else:
        return render_template('dive/elt_login_please.html');


@bp.route('/show/<int:dive_id>/plot/pressuregraph', methods = ['GET'])
def show_elt_pressure_graph(dive_id):
    return dive.get_cached_dive(dive_id).plot_pressure_graph(dive.get_gf_args_from_request());


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
    dp = dive.get_diveprofile_for_display(dive_id);
    # This will never return None, get_diveprofile_for_display will redirect/abort if necessary
    assert dp is not None;

    alldives = db_dive.get_all_dives();
    return render_template('dive/show.html',
                           dive = dp,
                           alldives = alldives,
                           modify_allowed = db_dive.is_modify_allowed(dp)
                           );


@bp.route('/show/any', methods = [ 'GET'])
def show_any():
    last_dive_id = session.get('last_dive_id', None);
    if last_dive_id is not None:
        return redirect(url_for('dive.show', dive_id = last_dive_id));
    dive_id = db_dive.get_any_dive_id();
    if dive_id is None:
        return redirect(url_for('dive.show_none'));
    else:
        return redirect(url_for('dive.show', dive_id = dive_id));


#
# Downloading CSV
#
@bp.route('/csv/<int:dive_id>')
def csv(dive_id):
    dp = dive.get_diveprofile_for_display(dive_id);
    if dp is None:
        abort(405);
    r = Response(dp.dataframe().to_csv(),
                 mimetype = "text/csv",
                 headers = { "Content-disposition": "attachment; filename=dive_%i.csv" % dive_id }
                 );
    return r;
