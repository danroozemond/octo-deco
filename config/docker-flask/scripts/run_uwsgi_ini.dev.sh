#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco
python3 setup.py build_ext --inplace
cd -
uwsgi $(dirname "$0")/uwsgi.ini --py-autoreload=1
