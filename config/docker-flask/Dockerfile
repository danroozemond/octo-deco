FROM python:3.8.2-buster

COPY data /data
RUN pip install -r /data/requirements.txt

# Idea is that you map the right drives and then run_flask.sh
CMD [ "/bin/bash" ]

