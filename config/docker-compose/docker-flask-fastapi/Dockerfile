FROM python:3.9-buster

COPY data /data
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /data/requirements.txt

# Idea is that you map the right drives in docker-compose and then use /scripts/run_...
CMD [ "/bin/bash" ]

