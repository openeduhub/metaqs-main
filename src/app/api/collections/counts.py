import uuid
from enum import Enum
from typing import Optional

from elasticsearch_dsl import A
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import ElasticResourceAttribute, oer_license
from app.elastic.elastic import ResourceType
from app.elastic.search import Search


class CollectionTreeCount(BaseModel):
    """
    A preliminary model to yield the total number of collections as well as counts for specific metrics,
    e.g. OER licence
    """

    node_id: uuid.UUID
    total: int
    counts: dict[str, int]
    oer_counts: Optional[dict[str, int]]
    oer_total: Optional[int]


_AGGREGATION_NAME = "collection_id"


class AggregationMappings(str, Enum):
    """
    Mappings of the elastic fields where facets should be built for each individual collection
    """

    lrt = ("properties.ccm:oeh_lrt_aggregated.keyword",)
    license = ("properties.ccm:commonlicense_key.keyword",)


def collection_counts_search(
    node_id: uuid.UUID, facet: AggregationMappings, oer_only: bool = False
) -> Search:
    search = (
        Search()
        .base_filters()
        .node_filter(resource_type=ResourceType.MATERIAL, node_id=node_id)
    )
    if oer_only:
        # Match with keyword for exact match, contrary to direct text matching, which is partial
        search = search.filter(
            {
                "terms": {
                    f"{ElasticResourceAttribute.LICENSES.path}.keyword": oer_license
                }
            }
        )
        # search = search.filter(Terms({f"{ElasticResourceAttribute.LICENSES.path}.keyword": oer_license})

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

    search.aggs.bucket(_AGGREGATION_NAME, material_agg)
    return search.extra(size=0)


async def collection_counts(
    node_id: uuid.UUID, facet: AggregationMappings, oer_only: bool = False
) -> Optional[list[CollectionTreeCount]]:
    response = collection_counts_search(node_id, facet, oer_only).execute()
    if response.success():
        return build_counts(response)


async def oer_collection_counts(
    node_id: uuid.UUID, facet: AggregationMappings
) -> Optional[list[CollectionTreeCount]]:
    counts = await collection_counts(node_id=node_id, facet=facet, oer_only=False)
    oer_counts = await collection_counts(node_id=node_id, facet=facet, oer_only=True)

    if counts and oer_counts:
        # merge counts and oer_counts
        for count in counts:
            for oer_count in oer_counts:
                if count.node_id == oer_count.node_id:
                    count.oer_counts = oer_count.counts
                    count.oer_total = oer_count.total
                    break
    return counts


def build_counts(response) -> list[CollectionTreeCount]:
    return [
        CollectionTreeCount(
            node_id=data["key"],
            counts={sub["key"]: sub["doc_count"] for sub in data.facet.buckets},
            total=data.doc_count,
        )
        for data in response.aggregations[_AGGREGATION_NAME].buckets
    ]


def oer_ratio(node_id: uuid.UUID) -> int:
    oer_statistics = collection_counts_search(node_id, AggregationMappings.license)
    response = oer_statistics.execute()
    oer_elements = 0
    oer_total = 0
    for data in response.aggregations[_AGGREGATION_NAME].buckets:
        for bucket in data["facet"]["buckets"]:
            oer_total += bucket["doc_count"]
            if bucket["key"] in oer_license:
                oer_elements += bucket["doc_count"]

    return round((oer_elements / oer_total) * 100)
