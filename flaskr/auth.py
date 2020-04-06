from flask import (
    Blueprint, flash, render_template
)

from ..deco.Buhlmann import Buhlmann;

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register')
def register():
    print("Hello, world");
    bm = Buhlmann(1,2,3,4);
    flash(bm.description());
    flash(':)');
    return render_template('auth/register.html')
