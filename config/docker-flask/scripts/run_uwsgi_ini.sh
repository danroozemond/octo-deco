#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco
pip install .
cd -
uwsgi $(dirname "$0")/uwsgi.ini
