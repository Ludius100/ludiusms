FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask gunicorn

COPY app.py config.py gunicorn.conf.py /app/
COPY services/ /app/services/
COPY routes/ /app/routes/
COPY modules/ /app/modules/

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
