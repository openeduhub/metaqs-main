from enum import Enum
from typing import Optional
from uuid import UUID

from elasticsearch_dsl import A
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.search import Search
from app.models import CollectionAttribute, ElasticResourceAttribute


class CollectionTreeCount(BaseModel):
    """
    A preliminary model to yield the total number of collections as well as counts for specific metrics, e.g. OER licence
    """

    noderef_id: UUID
    total: int
    counts: dict[str, int]


_AGGREGATION_NAME = "collection_id"


class AggregationMappings(str, Enum):
    """
    Mappings of the elastic fields where facets should be built for each individual collection
    """

    lrt = ("properties.ccm:oeh_lrt_aggregated.keyword",)
    license = ("properties.ccm:commonlicense_key.keyword",)


def collection_counts_search(node_id: UUID, facet: AggregationMappings) -> Search:
    s = Search().base_filters().material(id=node_id)
    material_agg = A(
        "terms", field="collections.nodeRef.id.keyword", size=ELASTIC_TOTAL_SIZE
    )
    material_agg.bucket(
        "facet",
        A(
            "terms",
            field=facet,
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


async def collection_counts(
    node_id: UUID, facet: AggregationMappings
) -> Optional[list[CollectionTreeCount]]:
    response = collection_counts_search(node_id, facet).execute()
    if response.success():
        return build_counts(response)


def build_counts(response) -> list[CollectionTreeCount]:
    return [
        CollectionTreeCount(
            noderef_id=data["key"],
            counts={sub["key"]: sub["doc_count"] for sub in data.facet.buckets},
            total=data.doc_count,
        )
        for data in response.aggregations[_AGGREGATION_NAME].buckets
    ]
