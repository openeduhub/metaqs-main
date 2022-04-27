Clone the main `repository`_ to the production machine when setting up the application.

.. _repository: https://github.com/openeduhub/metaqs-main

All services are deployed from Docker images -- either custom images build from the two other repositories or 3rd-party images.

Core services
-------------

Bring up the database:

These commands create a fresh postgres container and run the initial migrations to set up the required database schema::

    docker-compose up -d postgres
    docker-compose run dbt alembic upgrade head

Bring up remaining core services::

    docker-compose up -d

After these steps the output from docker ps should be similar to the following::

    CONTAINER ID   IMAGE                   COMMAND                   PORTS                                 NAMES
    e4d5eb5434d1   nginx:stable-alpine     "/docker-entrypoint.…"    0.0.0.0:80->80/tcp, :::80->80/tcp     nginx
    0b1fa78b9037   metaqs-api              "/start-reload.sh"        80/tcp                                api
    13d2f71dc4b9   metaqs-dbt              "/bin/sh -c 'dbt com…"    8580/tcp                              dbt
    5bc6326076f4   erikvl87/languagetool   "bash start.sh"           8010/tcp                              languagetool
    df4f2c3472be   postgres:14             "docker-entrypoint.s…"    5432/tcp                              postgres


Recovery::

    docker-compose up -d --no-deps --force-recreate api
