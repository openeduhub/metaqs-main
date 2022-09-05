FROM tiangolo/uvicorn-gunicorn:python3.9
WORKDIR /app
# Install Poetry
RUN apt-get update \
    && apt-get install -y ca-certificates \
    && curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false
COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
RUN poetry install --no-root
COPY ./ /app
