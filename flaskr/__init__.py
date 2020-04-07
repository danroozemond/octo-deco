import os

from flask import Flask, render_template;


# Define navigation row
def get_nav_items():
    return [ ('hello', 'Hello'),
             ('dive.show', 'Dive')
            ];


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        NAV_ITEMS=get_nav_items()
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    # blah
    @app.route('/')
    def index():
        return render_template('base.html')

    from . import auth;
    app.register_blueprint(auth.bp);

    # Dive
    from . import dive;
    app.register_blueprint(dive.bp);

    return app
