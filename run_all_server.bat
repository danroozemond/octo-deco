@echo off
set GOOGLE_OAUTH_JSON=config/docker-flask/scripts/client_secret.json.local

set FLASK_APP=octodeco/flaskr
set FLASK_ENV=development
set FLASK_SECRET_KEY=dev
set FLASK_CACHE_DIR=cache
set FLASK_CACHE_THRESHOLD=1000
set FLASK_PORT=5000
start flask run

set DB_PORT=8001
set DB_SQLITE=instance/flaskr.sqlite
start uvicorn octodeco.db.simple.app:app  --port %DB_PORT% --reload

echo "Stuff is started in new windows"