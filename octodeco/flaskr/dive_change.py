from . import dive;
from . import db_dive;
from .dive import bp;
from flask import (
    flash, redirect, url_for, request, abort, session
)


#
# Update (GF), delete, modify
#
@bp.route('/update/<int:dive_id>', methods = [ 'POST' ])
def update(dive_id):
    action = request.form.get('action');
    dp = dive.get_diveprofile_for_display(dive_id);
    if dp is None:
        abort(405);
    if action == 'Update Stops':
        olddecotime = dp.decotime();
        dp.set_gf(dp.gf_low_display, dp.gf_high_display, updateStops = True);
        flash('Recomputed stops (deco time: %i -> %i mins)' % (round(olddecotime), round(dp.decotime())));
        db_dive.store_dive(dp);
        dive.invalidate_cached_dive(dive_id);
        return redirect(url_for('dive.show', dive_id=dive_id));
    else:
        abort(405);


@bp.route('/delete/<int:dive_id>', methods = [ 'GET', 'POST' ])
def delete(dive_id):
    aff = db_dive.delete_dive(dive_id);
    if aff == 0:
        abort(405);
    flash('Dive %i is now history' % dive_id);
    dive.invalidate_cached_dive(dive_id);
    session[ 'last_dive_id' ] = None;
    return redirect(url_for('dive.show_any'));


@bp.route('/modify/meta/<int:dive_id>', methods = [ 'POST' ])
def modify_meta(dive_id):
    if request.form.get('action_update', '') != '':
        # Some input sanitation
        ipt_surface_section = max(0, min(120, request.form.get('ipt_surface_section', 0, type=int)));
        ipt_description = request.form.get('ipt_description')[:100];
        ipt_public = ( request.form.get('ipt_public', 'off').lower() == 'on')
        dp = dive.get_diveprofile_for_display(dive_id);
        if abs(dp.length_of_surface_section() - ipt_surface_section) > 0.1:
            dp.remove_surface_at_end();
            if ipt_surface_section > 0:
                flash("Added {} mins surface section".format(ipt_surface_section));
                dp.append_section(0, ipt_surface_section);
            else:
                flash("Removed surface section");
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
        dive.invalidate_cached_dive(dive_id);
        return redirect(url_for('dive.show', dive_id=dive_id));
    else:
        abort(405);


@bp.route('/modify/settings/<int:dive_id>', methods = [ 'POST' ])
def modify_settings(dive_id):
    if request.form.get('action_update_settings', '') != '':
        dp = dive.get_diveprofile_for_display(dive_id);
        # Update depth of last stop
        ipt_last_stop_depth = max(3, min(21, request.form.get('ipt_last_stop_depth', 3, type=int)));
        if ipt_last_stop_depth != dp._last_stop_depth:
            dp._last_stop_depth = ipt_last_stop_depth;
            dp.update_deco_info();
            flash("Change last stop to %i m" % ipt_last_stop_depth);
        # Update gas consumption settings
        ipt_gas_consmp_bottom = max(1, min(50, request.form.get('ipt_gas_consmp_bottom', 20, type=int)));
        ipt_gas_consmp_deco = max(1, min(50, request.form.get('ipt_gas_consmp_deco', 20, type=int)));
        if ipt_gas_consmp_bottom != dp._gas_consmp_bottom or ipt_gas_consmp_deco != dp._gas_consmp_deco:
            dp._gas_consmp_bottom = ipt_gas_consmp_bottom;
            dp._gas_consmp_deco = ipt_gas_consmp_deco;
            flash("Updated gas consumption figures");
        # Remove all stops
        ipt_remove_all_stops = ( request.form.get('ipt_remove_all_stops', 'off').lower() == 'on')
        if ipt_remove_all_stops:
            dp.update_stops( actually_add_stops = False );
            flash('Removed all stops');
        # Update database and invalidate cache
        db_dive.store_dive(dp);
        dive.invalidate_cached_dive(dive_id);
        return redirect(url_for('dive.show', dive_id=dive_id));
    else:
        abort(405);


@bp.route('/update/keep/<int:dive_id>', methods = [ 'POST' ])
def update_keep(dive_id):
    dp = dive.get_diveprofile_for_display(dive_id);
    if dp is not None:
        dp.is_ephemeral = False;
        flash('Keeping this dive permanently.');
        db_dive.store_dive(dp);
        dive.invalidate_cached_dive(dive_id);
        return redirect(url_for('dive.show', dive_id=dive_id));
    else:
        abort(405);
