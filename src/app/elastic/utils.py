from typing import Union

from elasticsearch_dsl import connections
from elasticsearch_dsl.response import AggResponse
from glom import merge

from app.core.config import (
    ELASTICSEARCH_CONNECTION_ALIAS,
    ELASTICSEARCH_TIMEOUT,
    ELASTICSEARCH_URL,
)
from app.core.logging import logger

from .fields import Field, FieldType


async def connect_to_elastic():
    logger.debug(f"Attempt to open connection: {ELASTICSEARCH_URL}")

    connections.create_connection(
        hosts=[ELASTICSEARCH_URL],
        timeout=ELASTICSEARCH_TIMEOUT,
        alias=ELASTICSEARCH_CONNECTION_ALIAS,
    )


async def close_elastic_connection():
    connections.remove_connection(alias=ELASTICSEARCH_CONNECTION_ALIAS)


def handle_text_field(qfield: Union[Field, str]) -> str:
    if isinstance(qfield, Field):
        qfield_key = qfield.path
        if qfield.field_type is FieldType.TEXT:
            qfield_key = f"{qfield_key}.keyword"
        return qfield_key
    else:
        return qfield


def merge_agg_response(
    agg: AggResponse, key: str = "key", result_field: str = "doc_count"
) -> dict:
    def op(carry: dict, bucket: dict):
        carry[bucket[key]] = bucket[result_field]

    return merge(agg.buckets, op=op)


def merge_composite_agg_response(
    agg: AggResponse, key: str, result_field: str = "doc_count"
) -> dict:
    def op(carry: dict, bucket: dict):
        carry[bucket["key"][key]] = bucket[result_field]

    return merge(agg.buckets, op=op)


# def fold_agg_response(
#     agg: AggResponse, key: str, result_field: str = "doc_count"
# ) -> dict:
#     return merge(agg)


# def map_reduce_agg_response(
#     agg: AggResponse, key: str, result_field: str = "doc_count"
# ) -> dict:
#     return merge(agg)
