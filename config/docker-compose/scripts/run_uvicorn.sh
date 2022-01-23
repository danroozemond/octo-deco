#!/bin/sh
. $(dirname "$0")/fastapi_settings.sh
env
rm /usr/bin/X11/X11 # known issue with python 3.8 & uvicorn
cd /octo-deco/octodeco/db
uvicorn $DB_APPNAME --host 0.0.0.0 --port $DB_PORT  --log-level info

