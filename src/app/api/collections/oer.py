import uuid

from app.api.collections.counts import (
    _AGGREGATION_NAME,
    AggregationMappings,
    collection_counts_search,
)


def oer_ratio(node_id: uuid.UUID) -> int:
    oer_statistics = collection_counts_search(node_id, AggregationMappings.license)
    response = oer_statistics.execute()
    oer_elements = 0
    oer_total = 0
    oer_license = ["CC_0", "PDM", "CC_BY", "CC_BY_SA"]
    for data in response.aggregations[_AGGREGATION_NAME].buckets:
        for bucket in data["facet"]["buckets"]:
            oer_total += bucket["doc_count"]
            if bucket["key"] in oer_license:
                oer_elements += bucket["doc_count"]

    return round((oer_elements / oer_total) * 100)
