# Please see LICENSE.md
from flask import (
    Blueprint, request, render_template, redirect, flash, url_for, abort
)

from . import db_dive, db_user;

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/')
@bp.route('/info')
def info():
    return render_template('user/info.html',
                           divecount = db_dive.get_dive_count(),
                           diveinfos = db_dive.get_all_dives(),
                           allsessions = db_user.get_all_sessions_for_user(),
                           user_details = db_user.get_user_details());


@bp.route('/update', methods = [ 'POST' ])
def update():
    action = request.form.get('action');
    if action == 'Destroy session':
        db_user.destroy_session();
        flash('Session was reset');
        return redirect(url_for('user.info'));
    elif action == 'Destroy entire profile':
        db_user.destroy_user_profile();
        flash('Your entire profile was removed');
        return redirect(url_for('user.info'));
    else:
        abort(405);

@bp.route('/logout')
def logout():
    db_user.destroy_session();
    flash('You were logged out');
    return redirect(url_for('user.info'));
