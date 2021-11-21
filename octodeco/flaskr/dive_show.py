from . import dive, user, db_api_dive;
from .dive import bp;
from .util.features import AllowedFeature as uft;
from flask import (
    redirect, url_for, request, abort, session, render_template, Response
)


#
# Showing the dive: separate elements
#
@bp.route('/show/<string:dive_id>/plot/profile', methods = ['GET'])
def show_elt_plot_profile(dive_id):
    cdp = dive.get_cached_dive(dive_id, user.get_user_details().user_id());
    return cdp.plot_profile(dive.get_gf_args_from_request());


@bp.route('/show/<string:dive_id>/plot/heatmap', methods = ['GET'])
def show_elt_plot_heatmap(dive_id):
    cdp = dive.get_cached_dive(dive_id, user.get_user_details().user_id());
    return cdp.plot_heatmap(dive.get_gf_args_from_request());


@bp.route('/show/<string:dive_id>/summary', methods = ['GET'])
def show_elt_summary_table(dive_id):
    cdp = dive.get_cached_dive(dive_id, user.get_user_details().user_id());
    reqargs = dive.get_gf_args_from_request();
    r1 = cdp.summary_table(reqargs);
    r2 = cdp.runtime_table(reqargs);
    r3 = cdp.gas_consumption_table();
    return '{}\n<h3>Runtime</h3>\n{}\n<h3>Gas consumption</h3>\n{}\n'.format(r1,r2,r3);


@bp.route('/show/<string:dive_id>/fulldata', methods = ['GET'])
def show_elt_full_table(dive_id):
    cdp = dive.get_cached_dive(dive_id, user.get_user_details().user_id());
    return cdp.full_table(dive.get_gf_args_from_request());


@bp.route('/show/<string:dive_id>/gfdecodata', methods = ['GET'])
def show_elt_gfdeco_table(dive_id):
    cdp = dive.get_cached_dive(dive_id, user.get_user_details().user_id());
    return cdp.gfdeco_table(dive.get_gf_args_from_request());


@bp.route('/show/<string:dive_id>/plot/pressuregraph', methods = ['GET'])
def show_elt_pressure_graph(dive_id):
    cdp = dive.get_cached_dive(dive_id, user.get_user_details().user_id());
    return cdp.plot_pressure_graph(dive.get_gf_args_from_request());


#
# Showing a dive: none, any, get, overview page
#
@bp.route('/show/none')
def show_none():
    return render_template('dive/show_none.html');


@bp.route('/show/get')
def show_get():
    dive_id = request.args.get("dive_id", '', type=str);
    return redirect(url_for('dive.show', dive_id=dive_id));


@bp.route('/show/<string:dive_id>', methods = ['GET'])
def show(dive_id):
    dp = dive.get_diveprofile_for_display(dive_id);
    if dp is None:
        return redirect(url_for('dive.show_any'));

    alldives = db_api_dive.get_all_dives();
    return render_template('dive/show.html',
                           dive = dp,
                           alldives = alldives,
                           modify_allowed = user.get_user_details().is_allowed(uft.DIVE_MODIFY, dive=dp)
                           );


@bp.route('/show/any', methods = [ 'GET'])
def show_any():
    last_dive_id = session.get('last_dive_id', None);
    if last_dive_id is not None:
        return redirect(url_for('dive.show', dive_id = last_dive_id));
    dive_id = db_api_dive.get_any_dive_id();
    if dive_id is None:
        return redirect(url_for('dive.show_none'));
    else:
        return redirect(url_for('dive.show', dive_id = dive_id));


#
# Downloading CSV
#
@bp.route('/csv/<string:dive_id>')
def csv(dive_id):
    dp = dive.get_diveprofile_for_display(dive_id);
    if dp is None:
        abort(403);
    r = Response(dp.dataframe().to_csv(),
                 mimetype = "text/csv",
                 headers = { "Content-disposition": "attachment; filename=dive_{}.csv".format(dive_id) }
                 );
    return r;
