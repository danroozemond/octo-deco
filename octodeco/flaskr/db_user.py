# Please see LICENSE.md
import uuid;

from flask import session, g;

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


def get_user_id():
    return get_user_details()['user_id'];


#
# Session / user manipulation
#

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
    user_id = get_user_id();
    cur = db.get_db().cursor();
    cur.execute('DELETE FROM dives WHERE user_id = ?', [ user_id ] );
    cur.execute('DELETE FROM sessions WHERE user_id = ?', [ user_id ]);
    cur.execute('DELETE FROM users WHERE user_id = ?', [ user_id ]);
    destroy_session();
    return cur.rowcount;
