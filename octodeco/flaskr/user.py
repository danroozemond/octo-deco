# Please see LICENSE.md
from flask import (
    Blueprint, request, render_template, redirect, flash, url_for, abort, g
)

from . import db_dive, db_user, auth;

bp = Blueprint('user', __name__, url_prefix='/user')


#
# Convenience class for user info
#
class UserDetails(dict):
    def __init__(self,*args,**kwargs) :
        dict.__init__(self,*args,**kwargs);

    def __repr__(self):
        return dict.__repr__(self);

    def is_logged_in(self):
        return self['google_sub'] is not None and self['google_sub'] != '';

    @property
    def is_admin(self):
        return self['is_admin'] == 1;

    @property
    def login_link(self):
        return auth.get_google_request_uri();

    @property
    def logout_link(self):
        return url_for('user.logout');


def get_user_details():
    if 'user_details' not in g:
        g.user_details = UserDetails(db_user.get_db_user_details());
    return g.user_details;


@bp.before_request
def load_user_details():
    get_user_details();


@bp.route('/')
@bp.route('/info')
def info():
    return render_template('user/info.html',
                           divecount = db_dive.get_dive_count(),
                           diveinfos = db_dive.get_all_dives(),
                           allsessions = db_user.get_all_sessions_for_user()
                           );


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
