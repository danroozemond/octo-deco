# Please see LICENSE.md
import requests, base64, json;

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
# Retrieve information
#
def get_dive_count():
    r = requests.get(ENDPOINT + 'dive/retrieve/count/', params = get_params());
    check_status_code(r);
    return r.json()['dive_count'];


def get_all_dives():
    r = requests.get(ENDPOINT + 'dive/retrieve/all/', params = get_params());
    check_status_code(r);
    return r.json();


def get_any_dive_id():
    r = requests.get(ENDPOINT + 'dive/retrieve/any/', params = get_params());
    check_status_code(r);
    if r.json() is None:
        return None;
    else:
        return r.json()['dive_id'];


#
# Retrieve dive
#
def get_one_dive(dive_id:int):
    r = requests.get(ENDPOINT + 'dive/retrieve/get/', params = get_params(dive_id = dive_id));
    check_status_code(r);
    row = r.json();
    if row is None:
        abort(404);
    assert row['user_id'] == user.get_user_details().user_id or row['is_public'] == 1;
    diveprofile = DiveProfileSer.loads(base64.b64decode(row['dive_serialized'].encode('utf-8')));
    diveprofile.dive_id = row['dive_id'];
    diveprofile.user_id = row['user_id'];
    return diveprofile;


#
# Storing a dive
#
def store_dive(diveprofile):
    # Check user_id
    if hasattr(diveprofile, 'user_id'):
        if diveprofile.user_id != user.get_user_details().user_id:
            abort(403);
    else:
        diveprofile.user_id = user.get_user_details().user_id;
    # Serialize & put request
    d = { 'dive_id': getattr(diveprofile, 'dive_id', None),
          'user_id': diveprofile.user_id,
          'dive_desc': diveprofile.description(),
          'is_public': diveprofile.is_public,
          'is_demo': diveprofile.is_demo_dive,
          'is_ephemeral': diveprofile.is_ephemeral,
          'dive_serialized': base64.b64encode(DiveProfileSer.dumps(diveprofile)).decode('utf-8')
          }
    r = requests.put(ENDPOINT + 'dive/write/store/', json = d);
    check_status_code(r);
    diveprofile.dive_id = r.json()['dive_id'];
    return diveprofile;