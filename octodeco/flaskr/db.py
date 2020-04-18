import sqlite3

from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types = sqlite3.PARSE_DECLTYPES,
            isolation_level = None
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close();


def init_db():
    db = get_db();
    with current_app.open_resource('sql/init-clean.sql') as f:
        db.executescript(f.read().decode('utf8'))
    print('Initialized the database using init-clean.sql');


def migrate_db(frv, tov):
    db = get_db();
    if frv == '0.3' and tov == '0.4':
        fname = 'sql/migrate-0.3-to-0.4.sql';
        with current_app.open_resource(fname) as f:
            db.executescript(f.read().decode('utf8'))
        print('Migrated data in the database using %s' % fname);
