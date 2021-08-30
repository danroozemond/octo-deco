FROM python:3.9.5-buster

COPY data /data
RUN pip install -r /data/requirements.txt

# Idea is that you map the right drives and then /scripts/run_flask.sh
CMD [ "/bin/bash" ]

