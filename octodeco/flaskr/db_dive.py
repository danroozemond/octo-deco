# Please see LICENSE.md
from . import db;
from .db_user import get_user_id;

from octodeco.deco import DiveProfileSer;

#
# Dive
# All functions are focused on the current user.
#
def get_dive_count():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT COUNT(*)
        FROM dives
        WHERE user_id = ?
        ''', [ get_user_id() ]
                );
    return cur.fetchone()[0];


def get_all_dives():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT dive_id, dive_desc
        FROM dives
        WHERE user_id = ?
        ''', [ get_user_id() ]
                );
    rows = cur.fetchall();
    return rows;


def get_any_dive_id():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT MIN(dive_id)
        FROM dives
        WHERE user_id = ?
        ''', [ get_user_id() ]
                );
    row = cur.fetchone();
    if row is None:
        return None
    return row[0];


def construct_dive_from_row(row):
    if row is None:
        return None;
    assert row['user_id'] == get_user_id();
    diveprofile = DiveProfileSer.loads(row['dive']);
    diveprofile.dive_id = row['dive_id'];
    return diveprofile;


def get_one_dive(dive_id:int):
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT user_id, dive_id, dive
        FROM dives
        WHERE user_id = ? and dive_id = ?
        ''', [ get_user_id(), dive_id ]
                      );
    return construct_dive_from_row(cur.fetchone());


def store_dive_update(diveprofile):
    dive_id = int(diveprofile.dive_id);
    if dive_id is None:
        raise AttributeError();
    cur = db.get_db().cursor();
    cur.execute('''
        UPDATE dives
        SET dive = ?, dive_desc = ?, is_demo = ?, last_update = datetime('now'), is_public = ?
        WHERE dive_id = ? AND user_id = ?;
        ''', [ DiveProfileSer.dumps(diveprofile), diveprofile.description(),
               diveprofile.is_demo_dive, diveprofile.is_public,
               dive_id, get_user_id() ]
               );
    assert cur.rowcount == 1;


def store_dive_new(diveprofile):
    cur = db.get_db().cursor();
    cur.execute('''
        INSERT INTO dives(user_id, dive)
        VALUES (?, 'xx');
        ''', [ get_user_id() ] );
    diveprofile.dive_id = cur.lastrowid;
    return store_dive_update(diveprofile);


def store_dive(diveprofile):
    try:
        store_dive_update(diveprofile);
    except AttributeError:
        store_dive_new(diveprofile);


def delete_dive(dive_id:int):
    cur = db.get_db().cursor();
    cur.execute('''
        DELETE
        FROM dives
        WHERE user_id = ? and dive_id = ?
        ''', [ get_user_id(), dive_id ]
                      );
    return cur.rowcount;
