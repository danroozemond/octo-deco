FROM python:3.8.2-buster

COPY data /app
RUN pip install -r /app/requirements.txt

CMD ["bash", "/app/go.sh"]

