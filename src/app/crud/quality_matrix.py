from typing import Union

from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

from app.core.constants import PROPERTIES, REPLICATION_SOURCE_ID
from app.core.logging import logger
from app.crud.elastic import add_base_match_filters
from app.crud.replication_sources import all_sources
from app.elastic import Search, qbool, qmatch

PROPERTY_TYPE = list[str]
QUALITY_MATRIX_RETURN_TYPE = list[dict[str, Union[str, float]]]


def extract_properties(hits: list[AttrDict]) -> PROPERTY_TYPE:
    return list(hits[0].to_dict()[PROPERTIES].keys())


def create_properties_search() -> Search:
    return add_base_match_filters(Search().source([PROPERTIES]))


def get_properties() -> PROPERTY_TYPE:
    s = create_properties_search()
    response = s.execute()
    return extract_properties(response.hits)


def create_empty_entries_search(
    properties: PROPERTY_TYPE, replication_source: str
) -> Search:
    s = add_base_match_filters(
        Search()
        .query(
            qbool(
                must=[
                    qmatch(
                        **{f"{PROPERTIES}.{REPLICATION_SOURCE_ID}": replication_source}
                    ),
                ]
            )
        )
        .source(includes=["aggregations"])
    )
    for keyword in properties:
        s.aggs.bucket(keyword, "missing", field=f"{PROPERTIES}.{keyword}.keyword")
    return s


def all_missing_properties(
    properties: PROPERTY_TYPE, replication_source: str
) -> Response:
    return create_empty_entries_search(properties, replication_source).execute()


def join_data(data, key):
    data |= {"metadatum": key}
    return data


def api_ready_output(raw_input: dict) -> QUALITY_MATRIX_RETURN_TYPE:
    return [join_data(data, key) for key, data in raw_input.items()]


def missing_fields_ratio(value: dict, total_count: int) -> float:
    return round((1 - value["doc_count"] / total_count) * 100, 2)


def missing_fields(
    value: dict, total_count: int, replication_source: str
) -> dict[str, float]:
    return {replication_source: missing_fields_ratio(value, total_count)}


async def quality_matrix() -> QUALITY_MATRIX_RETURN_TYPE:
    properties = get_properties()
    output = {k: {} for k in properties}
    for replication_source, total_count in all_sources().items():
        response = all_missing_properties(properties, replication_source)
        for key, value in response.aggregations.to_dict().items():
            output[key] |= missing_fields(value, total_count, replication_source)

    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)
