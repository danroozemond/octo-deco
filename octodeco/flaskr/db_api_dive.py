# Please see LICENSE.md
import requests, base64, json;

from flask import abort;

from . import app, user;
from octodeco.deco import DiveProfileSer;

ENDPOINT = app.setting_flask_db_endpoint;
assert ENDPOINT.endswith('/');


# All functions in this file are focused on the current user,
# no need to explicitly supply
def get_user_id_param():
    params = { 'user_id': user.get_user_details().user_id };
    return params;


def check_status_code_abort(resp):
    if not ( 200 <= resp.status_code < 300 ):
        abort(500);


#
# Retrieve information
#
def get_dive_count():
    r = requests.get(ENDPOINT + 'dive/retrieve/count/', params = get_user_id_param());
    check_status_code_abort(r);
    return r.json()['dive_count'];


def get_all_dives():
    r = requests.get(ENDPOINT + 'dive/retrieve/all/', params = get_user_id_param());
    check_status_code_abort(r);
    return r.json();


def get_any_dive_id():
    r = requests.get(ENDPOINT + 'dive/retrieve/any/', params = get_user_id_param());
    check_status_code_abort(r);
    if r.json() is None:
        return None;
    else:
        return r.json()['dive_id'];


#
# Retrieve dive
#
def get_one_dive(dive_id:int):
    r = requests.get(ENDPOINT + 'dive/retrieve/get/', params = {'dive_id':dive_id});
    row = r.json();
    if row is None:
        return None;
    # If we're here, we need a 200 status code
    check_status_code_abort(r);
    # Construct result
    diveprofile = DiveProfileSer.loads(base64.b64decode(row['dive_serialized'].encode('utf-8')));
    if not user.is_display_allowed(diveprofile):
        abort(405);
    diveprofile.dive_id = row['dive_id'];
    diveprofile.user_id = row['user_id'];
    return diveprofile;


#
# Storing a dive
#
def store_dive(diveprofile):
    # Check user_id
    if not user.is_modify_allowed(diveprofile):
        abort(405);
    if not hasattr(diveprofile, 'user_id'):
        diveprofile.user_id = user.get_user_details().user_id;
    # Serialize & put request
    d = { 'dive_id': getattr(diveprofile, 'dive_id', None),
          'user_id': diveprofile.user_id,
          'dive_desc': diveprofile.description(),
          'is_public': diveprofile.is_public,
          'is_demo': diveprofile.is_demo_dive,
          'is_ephemeral': diveprofile.is_ephemeral,
          'object_version' : diveprofile.db_version,
          'dive_serialized': base64.b64encode(DiveProfileSer.dumps(diveprofile)).decode('utf-8')
          }
    r = requests.put(ENDPOINT + 'dive/write/store/', json = d);
    check_status_code_abort(r);
    diveprofile.dive_id = r.json()['dive_id'];
    return diveprofile;


#
# Deleting a dive
#
def delete_dive(dive_id: int):
    # This check is a bit awkward, but we can improve it later
    if not user.is_modify_allowed(get_one_dive(dive_id)):
        print('User is not allowed to modify this dive {}'.format(dive_id));
        abort(405);
    # Do the deletion
    r = requests.delete(ENDPOINT + 'dive/write/delete/', params = {'dive_id':dive_id});
    check_status_code_abort(r);
    return r.json()['affected_count'];


#
# Admin: Batch migration
#
def migrate_all_profiles_to_latest():
    assert user.get_user_details().is_admin;
    r = requests.get(ENDPOINT + 'dive/retrieve/outdated_object_versions/',
                     params = { 'latest_version' : DiveProfileSer.CURRENT_VERSION});
    list_dive_ids = r.json();
    result = {'Timeout': False}; cnt = 0;
    for dive_id in list_dive_ids:
        dp = get_one_dive(dive_id);
        # At this point dp is automatically seralized and updated
        store_dive(dp);
        # Keep track
        print('Migrated dive_id {dive_id}');
        cnt += 1;
        # Limit, to avoid timeouts
        if cnt > 100:
            result['timeout'] = True;
            break;
    # Done
    return result;
