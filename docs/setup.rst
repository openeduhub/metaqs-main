The MetaQS Service is deployed as Docker container. The image will be build by the Github Action and is available at
`docker.edu-sharing.com/projects/oeh-redaktion/edusharing-projects-oeh-redaktion-metaqs-api` .

Bring up MetaQS together with nginx and postgres::

    docker-compose up -d

After these steps the output from docker ps should be similar to the following::

    CONTAINER ID   IMAGE                   COMMAND                   PORTS                                 NAMES
    e4d5eb5434d1   nginx:stable-alpine     "/docker-entrypoint.…"    0.0.0.0:80->80/tcp, :::80->80/tcp     nginx
    0b1fa78b9037   metaqs-api              "/start-reload.sh"        80/tcp                                api
    df4f2c3472be   postgres:14             "docker-entrypoint.s…"    5432/tcp                              postgres

Recovery::

    docker-compose up -d --no-deps --force-recreate api

Quality Matrix Timeline Cron Job
--------------------------------

Set up the crontab on your machine according to the file::

    scripts/crontab
