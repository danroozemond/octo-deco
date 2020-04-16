#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco/octodeco
flask run --host=0.0.0.0
