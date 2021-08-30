# Please see LICENSE.md
from flask import abort;

from . import db;
from .user import get_user_details;
from .app import cache;

from octodeco.deco import DiveProfileSer;

# All functions in this file are focused on the current user, no need
# to explicitly supply


#
# Store/modify
#
def store_dive(diveprofile):
    # A nice hook to call a cleanup function
    # cleanup_stale_dives();
    pass;


#
# Delete
#
def delete_dive(dive_id:int):
    cur = db.get_db().cursor();
    cur.execute('''
        DELETE
        FROM dives
        WHERE user_id = ? and dive_id = ?
        ''', [ get_user_details().user_id, dive_id ]
                      );
    return cur.rowcount;


#
# is_xx_allowed
#
def is_modify_allowed(diveprofile):
    dpu = getattr(diveprofile, 'user_id', None);
    return dpu == get_user_details().user_id;


def is_display_allowed(diveprofile):
    dpu = getattr(diveprofile, 'user_id', None);
    if dpu is None:
        return False;
    return dpu == get_user_details().user_id or diveprofile.is_public;


#
# batch migration
#
def migrate_all_profiles_to_latest():
    assert get_user_details().is_admin;
    cur = db.get_db().cursor();
    cur2 = db.get_db().cursor();
    rows = cur.execute('''
        SELECT dive_id, dive
        FROM dives
        ''');
    result = {'Timeout': False}; cnt = 0;
    for row in rows:
        dp, oldv, newv = DiveProfileSer.loads_with_version_info(row['dive']);
        if oldv == newv:
            continue;
        # Keep track
        strv = '{} -> {}'.format(oldv, newv);
        result[strv] = result.get(strv, 0) + 1;
        cnt += 1;
        # Do update
        cur2.execute('''
            UPDATE dives
            SET dive = ? 
            WHERE dive_id = ?
        ''', [ DiveProfileSer.dumps(dp), row['dive_id'] ] );
        # Limit, to avoid timeouts
        if cnt > 100:
            result['timeout'] = True;
            break;
    # Done
    return result;


@cache.memoize(timeout = 300)
def cleanup_stale_dives():
    # Every now and then, find old ephemeral dives and clean them up
    # Settings
    age_to_remove = 0.2;  # days (=~5 hrs)
    max_nr_to_remove = 10;
    # Do
    cur = db.get_db().cursor();
    cur.execute("""
                SELECT d.dive_id, julianday()-julianday(d.last_update) as age
                FROM dives d 
                WHERE d.is_ephemeral AND age > ?
                ORDER BY last_update
                LIMIT ?;
                """, [ age_to_remove, max_nr_to_remove ]);
    cur2 = db.get_db().cursor();
    for row in cur:
        dive_id = row['dive_id'];
        cur2.execute("DELETE FROM dives WHERE dive_id = ?", [ dive_id ] );
        print('Removed stale dive %i' % dive_id)
    return True;
