FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask gunicorn

COPY app.py config.py /app/
COPY services/ /app/services/

CMD ["gunicorn", "-b", "100.127.67.28:8090", "--workers", "1", "--threads", "4", "app:app"]
