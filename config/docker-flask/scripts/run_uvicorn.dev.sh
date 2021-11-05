#!/bin/sh
. $(dirname "$0")/fastapi_settings.sh
env
rm /usr/bin/X11/X11 # known issue with python 3.8 & uvicorn
cd /octo-deco
uvicorn $DB_APPNAME --host 0.0.0.0 --port $DB_PORT --reload --reload-dir /octo-deco/octodeco/db/ --log-level debug
