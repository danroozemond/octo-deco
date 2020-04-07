import uuid;

from flask import session;

from . import db;


#
# User
#
def get_user():
    if session.get('user_id', None) is None:
        session['user_id'] = uuid.uuid4();
    return session.get('user_id');


#
# Dive
#
def get_dives():
    dc = db.get_db();
    dives = dc.execute('''
        SELECT dive_id, dive
        FROM dives
        WHERE user_id = ?
        ''', [ str(get_user()) ]
    ).fetchall();
    print(dives);
    return len(dives);