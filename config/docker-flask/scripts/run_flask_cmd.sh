#!/bin/sh -v
. $(dirname "$0")/flask_settings.sh
env | grep FLASK
cd /octo-deco/octodeco
echo "Now try flask init-db or flask migrate-db"
chown www-data:www-data -R "$FLASK_INSTANCE_PATH"
chmod -R 775 "$FLASK_INSTANCE_PATH"
