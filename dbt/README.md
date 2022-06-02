# Build image

```bash
docker-compose build dbt
```

Tag image

```bash
```

```bash
docker push community.docker.edu-sharing.com/metaqs-dbt:latest
```


# Local install

Run
```bash
docker-compose up -d
cd dbt
RUN pip install --upgrade pip
RUN pip install alembic databases dbt-postgres
mkdir ~/.dbt
cp profiles.yml ~/.dbt/profiles.yml
alembic upgrade 0007
dbt seed && dbt build
```

In case of issues, may try `rm -rf dbt/target`.