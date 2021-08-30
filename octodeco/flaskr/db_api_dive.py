# Please see LICENSE.md
import requests;

from flask import abort;

from . import app, user;
from octodeco.deco import DiveProfileSer;

ENDPOINT = app.setting_flask_db_endpoint;
assert ENDPOINT.endswith('/');


# All functions in this file are focused on the current user,
# no need to explicitly supply
def get_params(dive_id = None):
    params = { 'user_id' : user.get_user_details().user_id };
    if dive_id is not None:
        params['dive_id'] = dive_id;
    return params;


def check_status_code(resp):
    if not ( 200 <= resp.status_code < 300 ):
        abort(500);


#
# Retrieve
#
def get_dive_count():
    r = requests.get(ENDPOINT + 'dive/retrieve/count/', params = get_params());
    check_status_code(r);
    return r.json()['dive_count'];


def get_all_dives():
    r = requests.get(ENDPOINT + 'dive/retrieve/all/', params = get_params());
    check_status_code(r);
    return r.json();
