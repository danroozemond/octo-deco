import pickle;
import uuid;

from flask import session, g, abort;

from . import db;


#
# User
#
def get_session_id():
    session_id = session.get('session_id', None);
    if session_id is None:
        # Migration
        if 'user_id' in session:
            print('Migrated from user_id to session_id');
            session_id = session.pop('user_id');
        else:
            print('Generated new session_id');
            session_id = uuid.uuid4();
        # Store
        session['session_id'] = session_id;
    return session_id;


def get_user_details():
    session_id = get_session_id();
    if 'user_details' not in g:
        cur = db.get_db().cursor();
        selectquery = '''
            SELECT u.user_id, u.google_email
            FROM sessions s LEFT JOIN users u
            ON s.user_id = u.user_id
            WHERE s.session_id = ?
            ''';
        cur.execute(selectquery, [ str(session_id) ] );
        row = cur.fetchone();
        if row is None:
            # Add details, try again
            cur.execute('INSERT INTO users(google_email) values(null)');
            user_id = cur.lastrowid;
            cur.execute("""
                        INSERT INTO sessions(session_id, user_id)
                        VALUES (?, ?)
                        """, [ str(session_id), user_id ] );
            cur.execute(selectquery, [ str(session_id) ] );
            row = cur.fetchone();
            assert row is not None;
        g.user_details = {
            'session_id' : session_id,
            'user_id' : row['user_id'],
            'google_email' : row['google_email']
        }
    return g.user_details;


def destroy_session():
    session_id = get_user_details()['session_id'];
    cur = db.get_db().cursor();
    cur.execute('''
        DELETE
        FROM sessions
        WHERE session_id = ?
        ''', [ str(session_id) ]
                );
    g.user_details = None;
    session.pop('session_id');


def user_reset_profile():
    user_id = get_user_details()['user_id'];
    cur = db.get_db().cursor();
    cur.execute('DELETE FROM dives WHERE user_id = ?', [ user_id ] );
    cur.execute('DELETE FROM sessions WHERE user_id = ?', [ user_id ]);
    cur.execute('DELETE FROM users WHERE user_id = ?', [ user_id ]);
    destroy_session();
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


def delete_dive(dive_id:int):
    current_user_id = str(get_user());
    cur = db.get_db().cursor();
    cur.execute('''
        DELETE
        FROM dives
        WHERE user_id = ? and dive_id = ?
        ''', [ current_user_id, dive_id ]
                      );
    return cur.rowcount;
