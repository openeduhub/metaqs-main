############
Architecture
############


# fixme: below image is outdated.

.. image:: assets/metaqs-service-architecture.png

Core services
=============

postgres
--------
- Is used to track the changes of the quality matrix over time.
- Uses postgres:14 docker image.

Environment variables::

    Variable	Value (recommended)
    POSTGRES_DB	analytics
    POSTGRES_USER	postgres
    POSTGRES_PASSWORD	postgres

nginx
-----

Find the nginx.conf at `nginx/nginx.conf.template` in the main repository.

Therein is also a `nginx-ssl.conf.template` for SSL setup.

Either of these is mounted into the nginx container (see docker-compose.yml).

API
---

Custom image based on tiangolo/uvicorn-gunicorn-fastapi.

Environment variables::

    Variable	Value	Description
    API_KEY		secures authenticated API endpoints
    ALLOWED_HOST	*
    POSTGRES_HOST	postgres	docker maps services in internal networks to service names
    LOG_LEVEL	info	options [error, warn, info, debug ]
    ELASTICSEARCH_URL		example: http://elastic-host:elastic-port

Optional services
=================

Sphinx
------

This project documentation can be exposed as a static website.
