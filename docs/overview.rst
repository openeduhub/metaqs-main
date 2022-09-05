********************
Project Repositories
********************

Code is placed in the `MetaQS main repository`_.

.. _MetaQS main repository: https://github.com/openeduhub/metaqs-main

Defines the service architecture in docker-compose.yml and contains the project documentation you are currently reading.

Background Task
----------------

Near real-time analytics functionality hinges on a background task running inside the fastapi service which periodically
updates statistics from elasticsearch. These statistics are then served to the user. This avoids long response times,
where the user would have to wait for slow elastics search queries to complete on every request.

