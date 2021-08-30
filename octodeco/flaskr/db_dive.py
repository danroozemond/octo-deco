# Please see LICENSE.md
from flask import abort;

from . import db;
from .user import get_user_details;
from .app import cache;

from octodeco.deco import DiveProfileSer;

# All functions in this file are focused on the current user, no need
# to explicitly supply


#
# Retrieve
#
def get_any_dive_id():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT MIN(dive_id)
        FROM dives
        WHERE user_id = ?
        ''', [ get_user_details().user_id ]
                );
    row = cur.fetchone();
    if row is None:
        return None
    return row[0];


def construct_dive_from_row(row):
    if row is None:
        return None;
    assert row['user_id'] == get_user_details().user_id or row['is_public'] == 1;
    diveprofile = DiveProfileSer.loads(row['dive']);
    diveprofile.dive_id = row['dive_id'];
    diveprofile.user_id = row['user_id'];
    return diveprofile;


def get_one_dive(dive_id:int):
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT user_id, dive_id, dive, is_public
        FROM dives
        WHERE dive_id = ? and (is_public or user_id = ?) 
        ''', [ dive_id, get_user_details().user_id ]
                      );
    return construct_dive_from_row(cur.fetchone());


#
# Store/modify
#
def _store_dive_update(diveprofile):
    # Check dive_id
    dive_id = int(diveprofile.dive_id);
    # Check user_id
    user_id = int(diveprofile.user_id);
    if user_id != get_user_details().user_id:
        abort(403);
    # Do stuff
    cur = db.get_db().cursor();
    cur.execute('''
        UPDATE dives
        SET dive = ?, dive_desc = ?, is_demo = ?, is_ephemeral = ?,  is_public = ?, last_update = datetime('now')
        WHERE dive_id = ? AND user_id = ?;
        ''', [ DiveProfileSer.dumps(diveprofile), diveprofile.description(),
               diveprofile.is_demo_dive, diveprofile.is_ephemeral, diveprofile.is_public,
               dive_id, get_user_details().user_id ]
               );
    assert cur.rowcount == 1;


def _store_dive_new(diveprofile):
    cur = db.get_db().cursor();
    cur.execute('''
        INSERT INTO dives(user_id, dive)
        VALUES (?, 'xx');
        ''', [ get_user_details().user_id ] );
    diveprofile.dive_id = cur.lastrowid;
    diveprofile.user_id = get_user_details().user_id;
    return _store_dive_update(diveprofile);


def store_dive(diveprofile):
    try:
        _store_dive_update(diveprofile);
    except AttributeError:
        _store_dive_new(diveprofile);
    # A nice hook to call a cleanup function
    cleanup_stale_dives();


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
