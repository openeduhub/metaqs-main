FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
WORKDIR /app
# Install Poetry
RUN apt-get update \
    && apt-get install -y ca-certificates \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/1.1.8/get-poetry.py | POETRY_HOME=/opt/poetry python \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false
COPY ./ /app
RUN poetry install --no-root
