# Please see LICENSE.md
import flask;
from flask import (
    Blueprint, request, render_template, redirect, flash, url_for
)

from . import data;

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/')
@bp.route('/info')
def info():
    return render_template('user/info.html',
                           # divecount = data.get_dive_count(),
                           # diveinfos = data.get_all_dives(),
                           user_details = data.get_user_details() );


@bp.route('/update', methods = [ 'POST' ])
def update():
    action = request.form.get('action');
    if action.startswith('Reset'):
        data.user_reset_profile();
        flash('User profile reset');
        return redirect(url_for('user.info'));
    else:
        flask.abort(405);
