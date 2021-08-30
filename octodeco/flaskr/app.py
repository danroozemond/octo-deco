import os
from datetime import timedelta

import click;
import flask;
from flask import Flask, session, url_for, g;
from flask_caching import Cache

from . import db;
from . import util;


# Define navigation row
def get_nav_items():
    return [ ('dive.show_any', '/dive/', 'Dive'),
             ('user.info', '/user/', 'User')
            ];


# Get settings
assert os.environ.get('FLASK_SECRET_KEY') is not None;
assert os.environ.get('GOOGLE_OAUTH_JSON') is not None;
assert os.environ.get('FLASK_PORT') is not None;
setting_secret_key = os.environ.get('FLASK_SECRET_KEY');
setting_instance_path = os.environ.get('FLASK_INSTANCE_PATH');
cache_dir = os.environ.get('FLASK_CACHE_DIR');
cache_threshold = int(os.environ.get('FLASK_CACHE_THRESHOLD', 10000));

# create and configure the app
app = Flask(__name__, instance_relative_config=True, instance_path = setting_instance_path)
app.config.from_mapping(
    SECRET_KEY = setting_secret_key,
    DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite'),
    NAV_ITEMS = get_nav_items(),
    CACHE_TYPE = "FileSystemCache",  # Flask-Caching related configs
    CACHE_DIR = cache_dir,
    CACHE_THRESHOLD = cache_threshold,
    CACHE_DEFAULT_TIMEOUT = 300
);

# Further settings
assert os.environ.get('FLASK_DB_ENDPOINT') is not None;
setting_flask_db_endpoint = os.environ.get('FLASK_DB_ENDPOINT');

# Create cache; on load flush it
cache = Cache(app);
cache.clear();

try:
    os.makedirs(app.instance_path)
except OSError:
    pass


# Session data
@app.before_request
def init_session():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=365);
    g.current_git_commit = util.CURRENT_GIT_COMMIT;
    g.current_git_branch = util.CURRENT_GIT_BRANCH;


@app.teardown_appcontext
def close_db(exception):
    db.close_db();


# Blueprints
from . import dive;
app.register_blueprint(dive.bp);
from . import user;
app.register_blueprint(user.bp);
from . import auth;
app.register_blueprint(auth.bp);
from . import admin;
app.register_blueprint(admin.bp);


#
# Separate Page definitions
#
@app.route('/')
def index():
    return flask.redirect( flask.url_for('dive.show_any') );


@app.route('/favicon.ico')
def favicon():
    return flask.redirect(url_for('static', filename='images/favicon/favicon.ico'));
