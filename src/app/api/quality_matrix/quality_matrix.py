from datetime import datetime
from typing import Union
from uuid import UUID

import sqlalchemy
from databases import Database
from elasticsearch_dsl import AttrDict, Q
from elasticsearch_dsl.response import Response

from app.api.quality_matrix.models import Forms, Timeline
from app.api.quality_matrix.utils import default_properties
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import COLLECTION_ROOT_ID, PROPERTIES, REPLICATION_SOURCE_ID
from app.core.logging import logger
from app.elastic.dsl import qbool, qmatch
from app.elastic.search import Search

PROPERTY_TYPE = list[str]
QUALITY_MATRIX_RETURN_TYPE = list[dict[str, Union[str, float]]]


def create_sources_search(aggregation_name: str):
    s = Search().base_filters()
    s.aggs.bucket(
        aggregation_name,
        "terms",
        field=f"{PROPERTIES}.{REPLICATION_SOURCE_ID}.keyword",
        size=ELASTIC_TOTAL_SIZE,
    )
    return s


def extract_sources_from_response(
    response: Response, aggregation_name: str
) -> dict[str, int]:
    return {
        entry["key"]: entry["doc_count"]
        for entry in response.aggregations.to_dict()[aggregation_name]["buckets"]
    }


def all_sources() -> dict[str, int]:
    aggregation_name = "unique_sources"
    s = create_sources_search(aggregation_name)
    response: Response = s.execute()
    return extract_sources_from_response(
        response=response, aggregation_name=aggregation_name
    )


def extract_properties(hits: list[AttrDict]) -> PROPERTY_TYPE:
    return list(set(list(hits[0].to_dict()[PROPERTIES].keys()) + default_properties()))


def create_properties_search() -> Search:
    return Search().base_filters().source([PROPERTIES])


def get_properties() -> PROPERTY_TYPE:
    s = create_properties_search()
    response = s.execute()
    return extract_properties(response.hits)


def create_empty_entries_search(
    properties: PROPERTY_TYPE,
    search_keyword: str,
    node_id: UUID,
    match_keyword: str,
) -> Search:
    s = (
        Search()
        .base_filters()
        .query(
            qbool(
                must=[
                    qmatch(**{match_keyword: search_keyword}),
                    Q("term", **{"path": node_id}),
                ]
            )
        )
        .source(includes=["aggregations"])
    )

    for keyword in properties:
        s.aggs.bucket(keyword, "missing", field=f"{PROPERTIES}.{keyword}.keyword")
    return s


def queried_missing_properties(
    properties: PROPERTY_TYPE,
    search_keyword: str,
    node_id: UUID,
    match_keyword: str,
) -> Response:
    return create_empty_entries_search(
        properties, search_keyword, node_id=node_id, match_keyword=match_keyword
    ).execute()


def join_data(data, key):
    return {"metadatum": key, "columns": data}


def api_ready_output(raw_input: dict) -> QUALITY_MATRIX_RETURN_TYPE:
    return [join_data(data, key) for key, data in raw_input.items()]


def missing_fields_ratio(value: dict, total_count: int) -> float:
    return round((1 - value["doc_count"] / total_count) * 100, 2)


def missing_fields(
    value: dict, total_count: int, search_keyword: str
) -> dict[str, float]:
    return {search_keyword: missing_fields_ratio(value, total_count)}


async def stored_in_timeline(
    data: QUALITY_MATRIX_RETURN_TYPE, database: Database, form: Forms
):
    await database.connect()
    await database.execute(
        sqlalchemy.insert(Timeline).values(
            {
                "timestamp": datetime.now().timestamp(),
                "quality_matrix": data,
                "form": form,
            }
        )
    )


async def items_in_response(response: Response) -> dict:
    return response.aggregations.to_dict().items()


async def source_quality(
    node_id: UUID = COLLECTION_ROOT_ID,
    match_keyword: str = f"{PROPERTIES}.{REPLICATION_SOURCE_ID}",
) -> QUALITY_MATRIX_RETURN_TYPE:
    properties = get_properties()
    columns = all_sources()
    mapping = {key: key for key in columns.keys()}  # identity mapping
    return await _quality_matrix(columns, mapping, match_keyword, node_id, properties)


async def _quality_matrix(
    columns, id_to_name_mapping, match_keyword, node_id, properties
):
    output = {k: {} for k in properties}
    for column_id, total_count in columns.items():
        if column_id in id_to_name_mapping.keys():
            response = queried_missing_properties(
                properties, column_id, node_id=node_id, match_keyword=match_keyword
            )
            for key, value in await items_in_response(response):
                output[key] |= missing_fields(
                    value, total_count, id_to_name_mapping[column_id]
                )
    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)
