import os, tempfile
from datetime import timedelta

import flask;
from flask import Flask, session, url_for, g;
from flask_caching import Cache

from .util import git;

_app = None;
_cache = None;
_db_endpoint = None;
def get_the_cache():
    # Ensure it's initialized
    assert _cache is not None;
    return _cache;
def get_db_endpoint():
    # Ensure it's initialized
    assert _db_endpoint is not None;
    return _db_endpoint;


# Define navigation row
def get_nav_items():
    return [ ('dive.show_any', '/dive/', 'Dive'),
             ('user.info', '/user/', 'User')
             ];


def create_flaskr_app():
    # Sorry
    global _app, _cache, _db_endpoint;
    # Verify some of the vital settings are there.
    assert os.environ.get('FLASK_SECRET_KEY') is not None;
    assert os.environ.get('FLASK_CACHE_DIR') is not None;
    assert os.environ.get('FLASK_DB_ENDPOINT') is not None;

    # Load settings
    setting_secret_key = os.environ.get('FLASK_SECRET_KEY');
    cache_dir = os.environ.get('FLASK_CACHE_DIR');
    cache_threshold = int(os.environ.get('FLASK_CACHE_THRESHOLD', 10000));
    _db_endpoint = os.environ.get('FLASK_DB_ENDPOINT');

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = setting_secret_key,
        NAV_ITEMS = get_nav_items(),
        CACHE_TYPE = "FileSystemCache",  # Flask-Caching related configs
        CACHE_DIR = cache_dir,
        CACHE_THRESHOLD = cache_threshold,
        CACHE_DEFAULT_TIMEOUT = 300
    );

    # Create cache; on load flush it
    _cache = Cache(app);
    _cache.clear();

    # Session data
    @app.before_request
    def init_session():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=365);
        g.current_git_commit = git.CURRENT_GIT_COMMIT;
        g.current_git_branch = git.CURRENT_GIT_BRANCH;

    # Blueprints
    from . import dive;
    app.register_blueprint(dive.bp);
    from . import user;
    app.register_blueprint(user.bp);
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

    return app;
