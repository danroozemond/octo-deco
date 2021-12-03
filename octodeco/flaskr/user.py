# Please see LICENSE.md
from flask import (
    Blueprint, render_template, g
)
from . import db_api_dive;
from .util.user import SimpleUser;

bp = Blueprint('user', __name__, url_prefix='/user');


def get_user_details():
    if 'user_details' not in g:
        g.user_details = SimpleUser();
    return g.user_details;


@bp.before_request
def load_user_details():
    get_user_details();


@bp.route('/')
@bp.route('/info')
def info():
    return render_template('user/info.html',
                           diveinfos = db_api_dive.get_all_dives(),
                           allsessions = []
                           );


