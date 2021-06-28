FROM python:3.9.5-buster

COPY data /data
RUN pip install -r /data/requirements.txt

# /scripts will be mapped by docker-compose
#COPY scripts /scripts

# Idea is that you map the right drives and then /scripts/run_flask.sh
CMD [ "/bin/bash" ]

