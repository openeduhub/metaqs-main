from elasticsearch_dsl.response import Response

from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import PROPERTIES, REPLICATION_SOURCE_ID
from app.crud.quality_matrix import add_base_match_filters
from app.elastic import Search


def extract_sources_from_response(
    response: Response, aggregation_name: str
) -> dict[str:int]:
    return {
        entry["key"]: entry["doc_count"]
        for entry in response.aggregations.to_dict()[aggregation_name]["buckets"]
    }


def create_sources_search(aggregation_name: str):
    s = add_base_match_filters(Search())
    s.aggs.bucket(
        aggregation_name,
        "terms",
        field=f"{PROPERTIES}.{REPLICATION_SOURCE_ID}.keyword",
        size=ELASTIC_TOTAL_SIZE,
    )
    return s


def all_sources() -> dict[str:int]:
    aggregation_name = "unique_sources"
    s = create_sources_search(aggregation_name)
    response: Response = s.execute()
    return extract_sources_from_response(
        response=response, aggregation_name=aggregation_name
    )
