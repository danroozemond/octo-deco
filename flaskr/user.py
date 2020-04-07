# Please see LICENSE.md
from flask import (
    Blueprint, render_template
)

from . import data;

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/')
@bp.route('/info')
def info():
    data.get_user();
    data.get_dives();
    return render_template('user/info.html');
