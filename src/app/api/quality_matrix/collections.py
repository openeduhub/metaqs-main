from uuid import UUID

from elasticsearch_dsl import Q
from elasticsearch_dsl.response import Response

from app.api.quality_matrix.quality_matrix import (
    QUALITY_MATRIX_RETURN_TYPE,
    _quality_matrix,
    add_base_match_filters,
    extract_sources_from_response,
    get_properties,
)
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import COLLECTION_ROOT_ID
from app.elastic.dsl import qbool
from app.elastic.search import Search

_TITLE_PROPERTY = "properties.cm:title"


def queried_collections(node_id: UUID = COLLECTION_ROOT_ID) -> dict[str, int]:
    """
    Query collection ID's and number of entries connected to this node id from Elasticsearch.

    :param node_id: Parent node ID, from which to search childrens.
    :return: Dictionary of node_id: total count of entries connected to this node id
    """
    aggregation_name = "unique_collections"
    s = add_base_match_filters(
        Search()
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


async def id_to_title_mapping(node_id: UUID):
    s = add_base_match_filters(
        Search()
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
    node_id: UUID, match_keyword: str = "path"
) -> QUALITY_MATRIX_RETURN_TYPE:
    mapping = await id_to_title_mapping(node_id)
    columns = queried_collections(node_id)
    properties = get_properties()
    return await _quality_matrix(columns, mapping, match_keyword, node_id, properties)
