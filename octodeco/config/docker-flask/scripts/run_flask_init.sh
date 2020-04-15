#!/bin/sh
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
flask init-db
chown www-data:www-data -R "$FLASK_INSTANCE_PATH"
chmod -R 775 "$FLASK_INSTANCE_PATH"
