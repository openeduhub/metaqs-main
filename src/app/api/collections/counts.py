import uuid
from enum import Enum
from typing import Optional

from elasticsearch_dsl import A
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.search import MaterialSearch


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


async def get_counts(node_id: uuid.UUID, facet: AggregationMappings) -> Optional[list[CollectionTreeCount]]:
    counts = await _collection_counts(node_id=node_id, facet=facet, oer_only=False)
    oer_counts = await _collection_counts(node_id=node_id, facet=facet, oer_only=True)

    if counts and oer_counts:
        # merge counts and oer_counts
        for count in counts:
            for oer_count in oer_counts:
                if count.node_id == oer_count.node_id:
                    count.oer_counts = oer_count.counts
                    count.oer_total = oer_count.total
                    break
    return counts


def _collection_counts_search(node_id: uuid.UUID, facet: AggregationMappings, oer_only: bool) -> MaterialSearch:
    if oer_only:
        search = MaterialSearch().oer_filter().collection_filter(collection_id=node_id, transitive=True)
    else:
        search = MaterialSearch().collection_filter(collection_id=node_id, transitive=True)
    material_agg = A("terms", field="collections.nodeRef.id.keyword", size=ELASTIC_TOTAL_SIZE)
    material_agg.bucket(
        "facet",
        A("terms", field=facet, size=ELASTIC_TOTAL_SIZE, missing="N/A"),
    )

    search.aggs.bucket(_AGGREGATION_NAME, material_agg)
    return search.extra(size=0)


async def _collection_counts(
    node_id: uuid.UUID, facet: AggregationMappings, oer_only: bool = False
) -> Optional[list[CollectionTreeCount]]:
    response = _collection_counts_search(node_id, facet, oer_only).execute()
    if response.success():
        return _build_counts(response)


def _build_counts(response) -> list[CollectionTreeCount]:
    return [
        CollectionTreeCount(
            node_id=data["key"],
            counts={sub["key"]: sub["doc_count"] for sub in data.facet.buckets},
            total=data.doc_count,
        )
        for data in response.aggregations[_AGGREGATION_NAME].buckets
    ]
