#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco
pip install --no-deps -e .
cd -
uwsgi $(dirname "$0")/uwsgi.ini --py-autoreload=1
