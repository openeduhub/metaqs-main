from uuid import UUID

from elasticsearch_dsl import A
from pydantic import BaseModel

from app.api.collections.models import CollectionAttribute
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.elastic import query_materials
from app.elastic.search import Search
from app.models import ElasticResourceAttribute


class PortalTreeCount(BaseModel):
    noderef_id: UUID
    counts: dict[str, int]


def query_portal_counts(node_id: UUID) -> Search:
    s = Search().query(query_materials(ancestor_id=node_id))
    material_agg = A(
        "terms", field="collections.nodeRef.id.keyword", size=ELASTIC_TOTAL_SIZE
    )
    material_agg.bucket(
        "lrt",
        A(
            "terms",
            field="properties.ccm:oeh_lrt_aggregated.keyword",
            size=ELASTIC_TOTAL_SIZE,
        ),
    )
    s.aggs.bucket("collection_id", material_agg)
    s = s.source(
        [
            ElasticResourceAttribute.NODEREF_ID.path,
            CollectionAttribute.TITLE.path,
            CollectionAttribute.PATH.path,
            CollectionAttribute.PARENT_ID.path,
        ]
    )[:ELASTIC_TOTAL_SIZE]
    return s


async def portal_counts(node_id: UUID) -> list[PortalTreeCount]:
    response = query_portal_counts(node_id).execute()
    if response.success():
        return build_counts(response)


def build_counts(response) -> list[PortalTreeCount]:
    result: list[PortalTreeCount] = []
    for data in response.aggregations["collection_id"].buckets:
        counts = {"total": data["doc_count"]}
        for sub in data.lrt.buckets:
            counts[sub["key"]] = sub["doc_count"]

        result.append(PortalTreeCount(noderef_id=data["key"], counts=counts))
    return result
