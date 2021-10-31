#!/bin/sh
. $(dirname "$0")/fastapi_settings.sh
env
cd /octo-deco
pip install -e .
cd -
uvicorn $DB_APPNAME  --port $DB_PORT --reload
