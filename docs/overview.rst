********************
Project Repositories
********************

Clone the main repository to the production machine when setting up the application.

All services are deployed from Docker images via docker-compose.

Code is placed in the `MetaQS main repository`_.

.. _MetaQS main repository: https://github.com/openeduhub/metaqs-main

Defines the service architecture in docker-compose.yml and contains the project documentation you are currently reading.

Background Tasks
----------------

Near real-time analytics functionality hinges on three different background tasks running inside the fastapi service:

- data import from elastic to postgres and subsequent analytics run in the analytics service,
- aggregate search stats from elastic and store in postgres,
- read from spellcheck_queue table in postgres, submit items to spellcheck service and store spellcheck errors in postgres.
