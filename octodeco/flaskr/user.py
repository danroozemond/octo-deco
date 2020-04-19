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
                           user_details = db_user.get_user_details());


@bp.route('/update', methods = [ 'POST' ])
def update():
    action = request.form.get('action');
    if action.startswith('Reset'):
        db_user.user_reset_profile();
        flash('User profile reset');
        return redirect(url_for('user.info'));
    else:
        abort(405);
