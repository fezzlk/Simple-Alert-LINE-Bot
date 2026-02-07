FROM python:3

WORKDIR /app

COPY ./ /app

RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt
RUN pip install -r /app/requirements.dev.txt

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} src:app"]
