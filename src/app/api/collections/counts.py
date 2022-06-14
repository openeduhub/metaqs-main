from uuid import UUID

from elasticsearch_dsl import A
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.elastic import query_materials
from app.elastic.search import Search
from app.models import CollectionAttribute, ElasticResourceAttribute


class PortalTreeCount(BaseModel):
    noderef_id: UUID
    total: int
    counts: dict[str, int]


_AGGREGATION_NAME = "collection_id"
# Mappings of the elastic fields where facets should be built for each individual collection
_AGGREGATION_MAPPINGS = {
    "lrt": "properties.ccm:oeh_lrt_aggregated.keyword",
    "license": "properties.ccm:commonlicense_key.keyword",
}


def query_portal_counts(node_id: UUID, facet: str) -> Search:
    s = Search().base_filters().query(query_materials(ancestor_id=node_id))
    material_agg = A(
        "terms", field="collections.nodeRef.id.keyword", size=ELASTIC_TOTAL_SIZE
    )
    material_agg.bucket(
        "facet",
        A(
            "terms",
            field=_AGGREGATION_MAPPINGS.get(facet),
            size=ELASTIC_TOTAL_SIZE,
        ),
    )
    s.aggs.bucket(_AGGREGATION_NAME, material_agg)
    s = s.source(
        [
            ElasticResourceAttribute.NODEREF_ID.path,
            CollectionAttribute.TITLE.path,
            CollectionAttribute.PATH.path,
            CollectionAttribute.PARENT_ID.path,
        ]
    )[:0]
    return s


async def portal_counts(node_id: UUID, facet: str) -> list[PortalTreeCount]:
    response = query_portal_counts(node_id, facet).execute()
    if response.success():
        return build_counts(response)


def counts(data):
    _counts = {}
    _counts.update({sub["key"]: sub["doc_count"] for sub in data["facet"].buckets})
    return _counts


def total(data):
    return data.doc_count


def build_counts(response) -> list[PortalTreeCount]:
    return [
        PortalTreeCount(noderef_id=data["key"], counts=counts(data), total=total(data))
        for data in response.aggregations[_AGGREGATION_NAME].buckets
    ]