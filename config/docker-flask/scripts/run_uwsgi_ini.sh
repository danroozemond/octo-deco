#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco
pip install -e .
cd -
uwsgi $(dirname "$0")/uwsgi.ini 
