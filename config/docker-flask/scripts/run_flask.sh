#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
flask run --host=0.0.0.0
