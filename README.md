# Overview

## Documentation Links

- [docker base image](https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker)
- [async pg client library](https://magicstack.github.io/asyncpg/current/index.html)
- [sqlalchemy (sync pg client)](https://docs.sqlalchemy.org/en/14/tutorial/index.html)
- [fastapi](https://fastapi.tiangolo.com/tutorial/)
- [pydantic](https://pydantic-docs.helpmanual.io/)
- [elasticsearch DSL query library](https://elasticsearch-dsl.readthedocs.io/en/latest/index.html)
- [glom - pythonic data parsing](https://glom.readthedocs.io/en/latest/index.html)
- [python http client](https://www.python-httpx.org/quickstart/)
- [python jsonrpc client](https://www.jsonrpcclient.com/en/stable/index.html)
- [python polling library](https://polling2.readthedocs.io/en/latest/index.html)


## How to add a new endpoint

If it is a realtime endpoint:

Add endpoint to respective router in `app/api/v1/realtime/api.py`

Add Elasticsearch query to CRUD in `app/crud/`

PostgreSQL:
- not needed

dbt:
- not needed

## How to structure an ES query

# Dev environment

Deploy docker-compose.yml to virtual machine.

## Setting up VM

Install docker

```bash
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

Use docker as root

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

Install docker-compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version  # Test the installation
```

## Preparing containers

Use 
```bash
docker-compose up
```

to download images for dbt, language tool, postgreSQL.

Fast API

DBT

```bash
docker-compose build dbt
docker push community.docker.edu-sharing.com/metaqs-dbt:latest
```

Superset
```bash
docker-compose build superset
docker push community.docker.edu-sharing.com/metaqs-superset:latest
```

## Preparing SQL

Launch postgres container and connect to `analytics` database.

```bash
docker-compose up -d postgres
docker-compose exec -u postgres postgres psql -d analytics
```

List all tables

```postgresql
\l
\dt
```

Get all relevant tables
```postgresql
SELECT * FROM pg_catalog.pg_tables
WHERE schemaname != 'information_schema' AND
schemaname != 'pg_catalog';
```

Create necessary tables



in prod:

analytics=# \l
                                 List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    |   Access privileges   
-----------+----------+----------+------------+------------+-----------------------
 analytics | postgres | UTF8     | en_US.utf8 | en_US.utf8 | 
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 | 
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
(4 rows)

analytics=# \dt
              List of relations
 Schema |      Name       | Type  |  Owner   
--------+-----------------+-------+----------
 public | alembic_version | table | postgres
(1 row)


 schemaname |                 tablename                 | tableowner | tablespace | hasindexes | hasrules | hastriggers | rowsecurity 
------------+-------------------------------------------+------------+------------+------------+----------+-------------+-------------
 public     | alembic_version                           | postgres   |            | t          | f        | f           | f
 raw        | collections_previous_run                  | postgres   |            | f          | f        | f           | f
 raw        | collections                               | postgres   |            | t          | f        | f           | f
 raw        | materials_previous_run                    | postgres   |            | f          | f        | f           | f
 store      | spellcheck                                | postgres   |            | t          | f        | f           | f
 store      | search_stats                              | postgres   |            | t          | f        | f           | f
 staging    | missing_fields                            | postgres   |            | f          | f        | f           | f
 staging    | collections                               | postgres   |            | f          | f        | f           | f
 staging    | pruned_resource_ids                       | postgres   |            | f          | f        | f           | f
 staging    | collection_material                       | postgres   |            | f          | f        | f           | f
 staging    | materials                                 | postgres   |            | f          | f        | f           | f
 staging    | spellcheck_queue                          | postgres   |            | f          | f        | f           | f
 staging    | collection_material_ext                   | postgres   |            | f          | f        | f           | f
 raw        | materials                                 | postgres   |            | t          | f        | f           | f
 staging    | spellcheck                                | postgres   |            | f          | f        | f           | f
 staging    | material_counts                           | postgres   |            | f          | f        | f           | f
 staging    | material_counts_by_error_field            | postgres   |            | f          | f        | f           | f
 staging    | material_counts_by_learning_resource_type | postgres   |            | f          | f        | f           | f
 staging    | materials_by_missing_field                | postgres   |            | f          | f        | f           | f

TODO: Create tables in pg
```postgresql
CREATE TABLE [raw.collections]
```

## Launch environment

Nginx must be configured with letsencrypt. Run

```bash
./init_letsencrypt.sh   
```

enter your desired domain. You need write permissions on that domain.

```bash
docker-compose -f docker-compose.dev.yml up
```