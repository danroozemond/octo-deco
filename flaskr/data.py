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


#
# Dive
#
def get_dives():
    cur = db.get_db().cursor();
    cur.execute('''
        SELECT dive_id, user_id, dive
        FROM dives
        WHERE user_id = ?;
        ''', [ str(get_user()) ]
                      );
    current_user_id = str(get_user());
    dives = [ ];
    while True:
        row = cur.fetchone()
        if row is None:
            break;
        assert row['user_id'] == current_user_id;
        diveprofile = pickle.loads(row['dive']);
        diveprofile.dive_id = row['dive_id'];
        dives.append(diveprofile);
    return dives;


def store_dive_new(diveprofile):
    cur = db.get_db().cursor();
    cur.execute('''
        INSERT INTO dives(user_id, dive)
        VALUES (?, ?);
        ''', [ str(get_user()), pickle.dumps(diveprofile) ]
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
        SET dive = ?
        WHERE dive_id = ? AND user_id = ?;
        ''', [ pickle.dumps(diveprofile), dive_id, str(get_user()) ]
               );
    assert cur.total_changes == 1;


def store_dive(diveprofile):
    try:
        store_dive_update(diveprofile);
    except AttributeError:
        store_dive_new(diveprofile);
