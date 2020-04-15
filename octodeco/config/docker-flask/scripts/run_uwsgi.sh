#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco
pip install -e .
cd /octo-deco/octodeco
uwsgi --processes 4 --http :5000 --uid www-data --gid www-data --master --mount /=flaskr:app
