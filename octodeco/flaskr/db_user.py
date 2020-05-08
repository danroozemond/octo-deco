# Please see LICENSE.md
import uuid;

from flask import session, g;

from . import db;
from .app import cache;


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
            session_id = uuid.uuid4();
        # Store
        session['session_id'] = session_id;
    return session_id;


@cache.memoize(timeout = 10)  # Short timeout
def _get_db_user_details(session_id):
    if 'db_user_details' not in g:
        cur = db.get_db().cursor();
        selectquery = '''
            SELECT u.*
            FROM sessions s INNER JOIN users u
            ON s.user_id = u.user_id
            WHERE s.session_id = ?
            ''';
        cur.execute(selectquery, [ str(session_id) ] );
        row = cur.fetchone();
        if row is None:
            # Add details, try again
            cur.execute('INSERT INTO users(last_activity) VALUES(datetime(\'now\'))');
            user_id = cur.lastrowid;
            cur.execute("""
                        INSERT INTO sessions(session_id, user_id)
                        VALUES (?, ?)
                        """, [ str(session_id), user_id ] );
            cur.execute(selectquery, [ str(session_id) ] );
            row = cur.fetchone();
            assert row is not None;
        g.db_user_details = { 'session_id' : session_id };
        g.db_user_details.update(dict(row));
        update_last_activity(row['user_id']);
    return g.db_user_details;


def get_db_user_details():
    session_id = get_session_id();
    return _get_db_user_details(session_id);


def get_user_id():
    return get_db_user_details()[ 'user_id' ];


#
# Session / user manipulation
#
def destroy_session():
    session_id = get_db_user_details()[ 'session_id' ];
    cur = db.get_db().cursor();
    cur.execute('''
        DELETE
        FROM sessions
        WHERE session_id = ?
        ''', [ str(session_id) ]
                );
    cache.delete_memoized(_get_db_user_details, session_id);
    g.user_details = None;
    session.clear();


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
# Authentication -> merge/allocate sessions
# (Google OAuth code is in auth.py)
#
def process_valid_google_login(userinfo_json):
    cur = db.get_db().cursor();
    cur.execute('SELECT user_id FROM users WHERE google_sub = ?', [ userinfo_json['sub']]);
    row = cur.fetchone();
    if row is None:
        # User previously unknown, update current user_id with these details
        cur.execute("""
                    UPDATE users 
                    SET google_sub = ?, google_given_name = ?, google_picture = ?, 
                        last_activity = datetime('now') 
                    WHERE user_id = ?
                    """,
                    [ userinfo_json['sub'], userinfo_json['given_name'], userinfo_json['picture'],
                      str(get_user_id()) ]);
    else:
        current_user_id = get_user_id();
        target_user_id = row['user_id'];
        # Update the session to tie to this user
        cur.execute("""UPDATE sessions SET user_id = ? WHERE session_id = ?""",
                    [ target_user_id, str(get_session_id())] );
        cur.execute("""DELETE FROM users WHERE user_id = ?""",
                    [ current_user_id ]);
        update_last_activity(target_user_id);
        # Update / remove existing dives
        cur.execute("""DELETE FROM dives WHERE user_id = ? AND is_demo = 1""",
                    [ current_user_id ]);
        cur.execute("""UPDATE dives SET user_id = ? WHERE user_id = ?""",
                    [ target_user_id, current_user_id ]);


#
# Keeping last_activity up to date, keeping the database clean
#
@cache.memoize(timeout = 60)
def update_last_activity(user_id):
    cur = db.get_db().cursor();
    cur.execute("""
                UPDATE users 
                SET last_activity = datetime('now') 
                WHERE user_id = ?""",
            [ user_id ]);
    return True;
