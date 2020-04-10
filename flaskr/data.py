import pickle;
import uuid;

from flask import session;

from . import db;


#
# User
#
def get_user():
    if session.get('user_id', None) is None:
        session[ 'user_id' ] = uuid.uuid4();
    return session.get('user_id');


def user_reset_profile():
    cur = db.get_db().cursor();
    cur.execute('''
        DELETE
        FROM dives
        WHERE user_id = ?
        ''', [ str(get_user()) ]
                );
    session['user_id'] = None;
    return cur.rowcount;


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
        ''', [ str(get_user()) ]
                );
    return cur.fetchone()[0];


def get_all_dives():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT dive_id, dive_desc
        FROM dives
        WHERE user_id = ?
        ''', [ str(get_user()) ]
                );
    rows = cur.fetchall();
    return rows;


def get_any_dive_id():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT MIN(dive_id)
        FROM dives
        WHERE user_id = ?
        ''', [ str(get_user()) ]
                );
    row = cur.fetchone();
    if row is None:
        return None
    return row[0];


def construct_dive_from_row(row):
    if row is None:
        return None;
    assert row['user_id'] == str(get_user());
    diveprofile = pickle.loads(row['dive']);
    diveprofile.dive_id = row['dive_id'];
    return diveprofile;


def get_one_dive(dive_id:int):
    current_user_id = str(get_user());
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT user_id, dive_id, dive
        FROM dives
        WHERE user_id = ? and dive_id = ?
        ''', [ current_user_id, dive_id ]
                      );
    return construct_dive_from_row(cur.fetchone());


def store_dive_new(diveprofile):
    cur = db.get_db().cursor();
    cur.execute('''
        INSERT INTO dives(user_id, dive, dive_desc)
        VALUES (?, ?, ?);
        ''', [ str(get_user()), pickle.dumps(diveprofile), diveprofile.description() ]
               );
    diveprofile.dive_id = cur.lastrowid;
    print("inserted dive; new id = %i" % cur.lastrowid);
    cur.close();


def store_dive_update(diveprofile):
    dive_id = int(diveprofile.dive_id);
    if dive_id is None:
        raise AttributeError();
    cur = db.get_db().cursor();
    cur.execute('''
        UPDATE dives
        SET dive = ?, dive_desc = ?
        WHERE dive_id = ? AND user_id = ?;
        ''', [ pickle.dumps(diveprofile), diveprofile.description(),
               dive_id, str(get_user()) ]
               );
    assert cur.rowcount == 1;


def store_dive(diveprofile):
    try:
        store_dive_update(diveprofile);
    except AttributeError:
        store_dive_new(diveprofile);
