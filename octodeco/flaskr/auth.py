# Please see LICENSE.md
from flask import (
    Blueprint, request, render_template, redirect, flash, url_for, abort
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/privacy-policy/')
def privacy_policy():
    return render_template('auth/privacy-policy.html');

@bp.route('/redirected')
def redirected():
    # Succesfull
    # TODO
    pass;
