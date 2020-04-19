import os
from datetime import timedelta

import click;
import flask;
from flask import Flask, session;


# Define navigation row
def get_nav_items():
    return [ ('dive.show_any', 'Dive'),
             ('user.info', 'User')
            ];


# Get settings
assert os.environ.get('FLASK_SECRET_KEY') is not None; # Won't store in version control
assert os.environ.get('GOOGLE_OAUTH_JSON') is not None; # Won't store in version control
setting_secret_key = os.environ.get('FLASK_SECRET_KEY');
setting_instance_path = os.environ.get('FLASK_INSTANCE_PATH');

# create and configure the app
app = Flask(__name__, instance_relative_config=True, instance_path = setting_instance_path)
app.config.from_mapping(
    SECRET_KEY = setting_secret_key,
    DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite'),
    NAV_ITEMS = get_nav_items()
);
try:
    os.makedirs(app.instance_path)
except OSError:
    pass


#
# Database manipulations
#
@click.command('init-db')
@flask.cli.with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    from . import db;
    db.init_db()
    click.echo('Initialized the database in %s' % app.config['DATABASE'])

@click.command('migrate-db')
@click.argument('frv')
@click.argument('tov')
@flask.cli.with_appcontext
def migrate_db_command(frv, tov):
    """Migrate from one data version to another"""
    from . import db;
    db.migrate_db(frv,tov)
    click.echo('Migrated the database in %s' % app.config['DATABASE'])

app.cli.add_command(init_db_command);
app.cli.add_command(migrate_db_command);


# Session data
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=365);


# Blueprints
from . import dive;
app.register_blueprint(dive.bp);
from . import user;
app.register_blueprint(user.bp);
from . import auth;
app.register_blueprint(auth.bp);


#
# Separate Page definitions
#
@app.route('/')
def index():
    return flask.redirect( flask.url_for('dive.show_any') );
