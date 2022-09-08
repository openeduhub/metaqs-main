"""
Functionality that is shared between different endpoints.
"""

import uuid
from fastapi import HTTPException

from elasticsearch_dsl import A

from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import OER_LICENSES
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import MaterialSearch


def oer_ratio(collection_id: uuid.UUID) -> int:
    """
    Query the percentage of OER materials of given collection from elasticsearch.
    """
    # Note:
    # It is important to not group by collection here, as materials can be in multiple collections
    # and hence some materials would be counted multiple times into OER vs Non-OER if we would first
    # group by collection and then aggregate over the collection groups.
    # fmt: off
    search = (
        MaterialSearch()
        .collection_filter(collection_id=collection_id, transitive=True)
        .extra(size=0, from_=0)
    )
    # fmt: on

    search.aggs.bucket(
        "materials_by_license",
        A("terms", field=ElasticResourceAttribute.LICENSES.keyword, size=ELASTIC_TOTAL_SIZE, missing="N/A"),
    )

    response = search.execute()
    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to query elasticsearch")

    oer = 0
    total = 0
    for bucket in response.aggregations["materials_by_license"]["buckets"]:
        total += bucket["doc_count"]
        if bucket["key"] in OER_LICENSES:
            oer += bucket["doc_count"]
    return round((oer / total) * 100)
