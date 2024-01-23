from elasticsearch_dsl import connections

from app.core.config import ELASTICSEARCH_TIMEOUT, ELASTICSEARCH_URL
from app.core.logging import logger


def connect_to_elastic():
    logger.debug(f"Attempt to open connection: {ELASTICSEARCH_URL}")
    connections.create_connection(hosts=[ELASTICSEARCH_URL], timeout=ELASTICSEARCH_TIMEOUT)
