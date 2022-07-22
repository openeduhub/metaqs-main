# Taken form https://github.com/tiangolo/uvicorn-gunicorn-docker/blob/master/docker-images/python3.9.dockerfile
#  but adapted for Python 3.10
FROM python:3.10

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

COPY ./gunicorn_conf.py /gunicorn_conf.py

COPY ./start_reload.sh /start_reload.sh
RUN chmod +x /start_reload.sh

COPY ./app /app
WORKDIR /app/

ENV PYTHONPATH=/app



WORKDIR /app
# Install Poetry
RUN apt-get update \
    && apt-get install -y ca-certificates \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/1.1.8/get-poetry.py | POETRY_HOME=/opt/poetry python \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false
COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
RUN poetry install --no-root
COPY ./ /app
