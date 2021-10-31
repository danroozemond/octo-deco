# Please see LICENSE.md
import flask;
from . import app, user;

ENDPOINT = app.setting_flask_db_endpoint;
assert ENDPOINT.endswith('/');


def get_user_id_param():
    params = { 'user_id': user.get_user_details().user_id() };
    return params;


def check_status_code_abort(resp):
    if not ( 200 <= resp.status_code < 300 ):
        flask.abort(500);