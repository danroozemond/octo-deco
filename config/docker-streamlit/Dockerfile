FROM python:3.8.2-buster

COPY data /app
RUN pip install -r /app/requirements.txt

CMD [ "streamlit", "run", "/app2/octo-deco/run_streamlit_ui.py" ]

