FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY ./ /app

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} src:app"]
