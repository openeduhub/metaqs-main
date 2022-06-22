from typing import Union

from elasticsearch_dsl import connections

from app.core.config import ELASTICSEARCH_TIMEOUT, ELASTICSEARCH_URL
from app.core.logging import logger

from .fields import ElasticField, ElasticFieldType


async def connect_to_elastic():
    logger.debug(f"Attempt to open connection: {ELASTICSEARCH_URL}")

    connections.create_connection(
        hosts=[ELASTICSEARCH_URL], timeout=ELASTICSEARCH_TIMEOUT
    )


def handle_text_field(qfield: Union[ElasticField, str]) -> str:
    if isinstance(qfield, ElasticField):
        qfield_key = qfield.path
        if qfield.field_type is ElasticFieldType.TEXT:
            qfield_key = f"{qfield_key}.keyword"
        return qfield_key
    else:
        return qfield
