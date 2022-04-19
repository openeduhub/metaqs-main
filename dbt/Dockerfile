FROM python:3.9
RUN pip install --upgrade pip
RUN pip install alembic databases dbt-postgres
COPY ./profiles.yml /root/.dbt/profiles.yml
COPY ./ /dbt
WORKDIR /dbt
EXPOSE 8580