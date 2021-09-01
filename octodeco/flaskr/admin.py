# Please see LICENSE.md
from flask import (
    Blueprint, render_template, redirect, flash, url_for, abort
)

from . import db_dive, db_api_dive, user;

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.before_request
def load_user_details():
    ud = user.get_user_details();
    if not ud.is_admin:
        abort(403);


@bp.route('/')
@bp.route('/info')
def info():
    return render_template('admin/info.html');


@bp.route('/migrate/all', methods = [ 'POST' ])
def migrate_all():
    res = db_api_dive.migrate_all_profiles_to_latest();
    flash('Migrate all: ' + str(res));
    return redirect(url_for('admin.info'));



