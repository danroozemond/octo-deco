@echo off
set FLASK_APP=octodeco/flaskr
set FLASK_ENV=development
set FLASK_SECRET_KEY=dev
set GOOGLE_OAUTH_JSON=config/docker-flask/scripts/client_secret.json.local
flask run
