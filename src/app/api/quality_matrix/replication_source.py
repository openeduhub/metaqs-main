import uuid

from elasticsearch_dsl import AttrDict, Q
from elasticsearch_dsl.response import Response

from app.api.quality_matrix.models import QualityOutput
from app.api.quality_matrix.utils import default_properties
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import COLLECTION_ROOT_ID
from app.core.logging import logger
from app.core.models import (
    ElasticResourceAttribute,
    metadata_hierarchy,
    required_collection_properties,
)
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import ResourceType
from app.elastic.search import Search

PROPERTY_TYPE = list[str]
PROPERTIES = "properties"


def create_sources_search(aggregation_name: str, node_id: uuid.UUID) -> Search:
    search = (
        Search()
        .base_filters()
        .type_filter(ResourceType.MATERIAL)
        .filter(Q("term", **{f"{ElasticResourceAttribute.PATH.path}": node_id}))
    )
    search.aggs.bucket(
        aggregation_name,
        "terms",
        field=f"{ElasticResourceAttribute.REPLICATION_SOURCE.path}.keyword",
        size=ELASTIC_TOTAL_SIZE,
    )
    return search


def extract_sources_from_response(
    response: Response, aggregation_name: str
) -> dict[str, int]:
    return {
        entry["key"]: entry["doc_count"]
        for entry in response.aggregations.to_dict()[aggregation_name]["buckets"]
    }


def all_sources(node_id: uuid.UUID) -> dict[str, int]:
    aggregation_name = "unique_sources"
    s = create_sources_search(aggregation_name, node_id)
    response: Response = s.execute()
    return extract_sources_from_response(
        response=response, aggregation_name=aggregation_name
    )


def extract_properties(hits: list[AttrDict]) -> PROPERTY_TYPE:
    return list(set(list(hits[0].to_dict()[PROPERTIES].keys()) + default_properties()))


def create_properties_search() -> Search:
    return Search().base_filters().source([PROPERTIES])


def get_properties(use_required_properties_only: bool = True) -> PROPERTY_TYPE:
    if use_required_properties_only:
        return [entry.split(".")[-1] for entry in required_collection_properties.keys()]
    else:
        search = create_properties_search()
        response = search.execute()
        return extract_properties(response.hits)


def create_empty_entries_search(
    properties: PROPERTY_TYPE,
    search_keyword: str,
    node_id: uuid.UUID,
    match_keyword: str,
) -> Search:
    search = (
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
        search.aggs.bucket(keyword, "missing", field=f"{PROPERTIES}.{keyword}.keyword")
    return search


def queried_missing_properties(
    properties: PROPERTY_TYPE,
    search_keyword: str,
    node_id: uuid.UUID,
    match_keyword: str,
) -> Response:
    return create_empty_entries_search(
        properties, search_keyword, node_id=node_id, match_keyword=match_keyword
    ).execute()


def missing_fields_ratio(value: dict, total_count: int) -> float:
    return round((1 - value["doc_count"] / total_count) * 100, 2)


def missing_fields(
    value: dict, total_count: int, search_keyword: str
) -> dict[str, float]:
    return {search_keyword: missing_fields_ratio(value, total_count)}


async def items_in_response(response: Response) -> dict:
    return response.aggregations.to_dict().items()


async def source_quality(
    node_id: uuid.UUID = COLLECTION_ROOT_ID,
    match_keyword: str = ElasticResourceAttribute.REPLICATION_SOURCE.path,
) -> tuple[list[QualityOutput], dict[str, int]]:
    properties = get_properties()
    columns = all_sources(node_id)
    mapping = {key: key for key in columns.keys()}  # identity mapping
    quality = await _quality_matrix(
        columns, mapping, match_keyword, node_id, properties
    )
    return quality, columns


def sort_output_to_hierarchy(data: list[QualityOutput]) -> list[QualityOutput]:
    output = []
    for order in metadata_hierarchy:
        output.append(QualityOutput(row_header=order.title, level=1, columns={}))
        for node in order.children:
            row = list(
                filter(
                    lambda entry: entry.row_header == node.path.path.split(".")[-1],
                    data,
                )
            )
            if len(row) == 1:
                output.append(row[0])
    return output


async def _quality_matrix(
    columns, id_to_name_mapping, match_keyword, node_id, properties
) -> list[QualityOutput]:
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
    output = [
        QualityOutput(row_header=key, columns=data, level=2)
        for key, data in output.items()
    ]

    return sort_output_to_hierarchy(output)
