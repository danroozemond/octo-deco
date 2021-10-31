@echo off
set FLASK_APP=octodeco/flaskr
set FLASK_ENV=development
set FLASK_SECRET_KEY=dev
set FLASK_CACHE_DIR=cache
set FLASK_CACHE_THRESHOLD=1000
set FLASK_PORT=5000
set FLASK_DB_ENDPOINT=http://localhost:8001/
start flask run --port=%FLASK_PORT%

set DB_PORT=8001
set DB_SQLITE=instance/flaskr.sqlite
start uvicorn octodeco.db.simple.app:app  --port %DB_PORT% --reload

echo Stuff is started in new windows