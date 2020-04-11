#!/bin/sh
export FLASK_APP=flaskr
export FLASK_INSTANCE_PATH=/flask_instance
flask run --host=0.0.0.0
