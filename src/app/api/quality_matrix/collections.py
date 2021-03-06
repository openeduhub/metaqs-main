import uuid

from elasticsearch_dsl import Q
from elasticsearch_dsl.response import Response

from app.api.quality_matrix.models import QualityOutput
from app.api.quality_matrix.replication_source import (
    _quality_matrix,
    extract_sources_from_response,
    get_properties,
)
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import COLLECTION_ROOT_ID
from app.elastic.dsl import qbool
from app.elastic.search import Search

_TITLE_PROPERTY = "properties.cm:title"


def queried_collections(node_id: uuid.UUID = COLLECTION_ROOT_ID) -> dict[str, int]:
    """
    Query collection ID's and number of entries connected to this node id from Elasticsearch.

    param node_id: Parent node ID, from which to search childrens.
    :return: Dictionary of node_id: total count of entries connected to this node id
    """
    aggregation_name = "unique_collections"
    s = (
        Search()
        .base_filters()
        .query(
            qbool(
                must=[
                    Q("term", **{"path": node_id}),
                ]
            )
        )
        .source(includes=["aggregations", _TITLE_PROPERTY])
    )

    s.aggs.bucket(aggregation_name, "terms", field="path", size=ELASTIC_TOTAL_SIZE)

    response: Response = s.execute()
    return extract_sources_from_response(response, aggregation_name)


async def id_to_title_mapping(node_id: uuid.UUID) -> dict[str, str]:
    s = (
        Search()
        .base_filters()
        .query(
            qbool(
                must=[
                    Q("term", **{"path": node_id}),
                    Q("exists", field=_TITLE_PROPERTY),
                ]
            )
        )[:ELASTIC_TOTAL_SIZE]
        .source(includes=["nodeRef.id", _TITLE_PROPERTY])
    )

    response: Response = s.execute()
    mapping = {hit.nodeRef.id: hit.properties["cm:title"] for hit in response.hits}
    return mapping


async def collection_quality(
    node_id: uuid.UUID, match_keyword: str = "path"
) -> tuple[list[QualityOutput], dict[str, int]]:
    mapping = await id_to_title_mapping(node_id)
    columns = queried_collections(node_id)
    properties = get_properties()
    quality_data = await _quality_matrix(
        columns, mapping, match_keyword, node_id, properties
    )
    quality_data = transpose(quality_data, [name for name in mapping.values()])
    return quality_data, {prop: 0 for prop in properties}


def transpose(entries: list[QualityOutput], columns: list[str]) -> list[QualityOutput]:
    rows = [entry.row_header for entry in entries]
    output = []
    for column in columns:
        new_columns = {}
        for row_header in rows:
            entry = list(filter(lambda line: line.row_header == row_header, entries))
            if len(entry) == 1 and column in entry[0].columns:
                new_columns.update({row_header: entry[0].columns[column]})

        new_row = QualityOutput(
            row_header=column, columns=new_columns, level=2
        )  # Must be level 2 for frontend
        output.append(new_row)
    return output
