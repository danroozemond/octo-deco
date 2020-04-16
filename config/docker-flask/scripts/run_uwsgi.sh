#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco
pip install -e .
cd /octo-deco/octodeco
uwsgi --processes 4 --http-socket :5000 --master \
	--stats :9191 \
	--uid www-data --gid www-data \
	--mount /=flaskr:app
