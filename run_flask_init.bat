@echo off
set FLASK_APP=octodeco/flaskr
set FLASK_ENV=development
set FLASK_SECRET_KEY=dev
flask init-db
