#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
flask init-db
