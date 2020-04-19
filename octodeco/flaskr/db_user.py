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
            SELECT u.*
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
        g.user_details = { 'session_id' : session_id };
        g.user_details.update(dict(row));
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


def destroy_user_profile():
    user_id = get_user_id();
    cur = db.get_db().cursor();
    cur.execute('DELETE FROM dives WHERE user_id = ?', [ user_id ] );
    cur.execute('DELETE FROM sessions WHERE user_id = ?', [ user_id ]);
    cur.execute('DELETE FROM users WHERE user_id = ?', [ user_id ]);
    destroy_session();
    return cur.rowcount;


def get_all_sessions_for_user():
    user_id = get_user_id();
    cur = db.get_db().cursor();
    cur.execute('SELECT session_id FROM sessions WHERE user_id = ?', [ user_id ]);
    return [ row['session_id'] for row in cur.fetchall() ];


#
# Auth
#
def process_valid_google_login(userinfo_json):
    cur = db.get_db().cursor();
    cur.execute('SELECT user_id FROM users WHERE google_sub = ?', [ userinfo_json['sub']]);
    row = cur.fetchone();
    if row is None:
        # User previously unknown, update current user_id with these details
        cur.execute("""
                    UPDATE users 
                    SET google_sub = ?, google_given_name = ?, google_picture = ?
                    WHERE user_id = ?
                    """,
                    [ userinfo_json['sub'], userinfo_json['given_name'], userinfo_json['picture'],
                      str(get_user_id()) ]);
    else:
        # TODO - merge the two sessions
        pass;


