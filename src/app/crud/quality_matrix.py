from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

from app.core.constants import PROPERTIES, REPLICATION_SOURCE_ID
from app.core.logging import logger
from app.crud.elastic import base_match_filter
from app.elastic import Search, qbool, qmatch

PROPERTY_TYPE = list[str]


def add_base_match_filters(search: Search) -> Search:
    for entry in base_match_filter:
        search = search.query(entry)
    return search


def create_sources_search(aggregation_name: str):
    s = add_base_match_filters(Search())
    s.aggs.bucket(
        aggregation_name, "terms", field=f"{PROPERTIES}.{REPLICATION_SOURCE_ID}.keyword"
    )
    return s


def extract_sources_from_response(
    response: Response, aggregation_name: str
) -> dict[str:int]:
    return {
        entry["key"]: entry["doc_count"]
        for entry in response.aggregations.to_dict()[aggregation_name]["buckets"]
    }


def all_sources() -> dict[str:int]:
    aggregation_name = "unique_sources"
    s = create_sources_search(aggregation_name)
    response: Response = s.execute()
    return extract_sources_from_response(
        response=response, aggregation_name=aggregation_name
    )


def extract_properties(hits: list[AttrDict]) -> PROPERTY_TYPE:
    return list(hits[0].to_dict()[PROPERTIES].keys())


def create_properties_search() -> Search:
    return add_base_match_filters(Search().source([PROPERTIES]))


def get_properties() -> PROPERTY_TYPE:
    s = create_properties_search()
    response = s.execute()
    return extract_properties(response.hits)


def create_empty_entries_search(
    properties: PROPERTY_TYPE, replication_source: str
) -> Search:
    s = add_base_match_filters(
        Search()
        .query(
            qbool(
                must=[
                    qmatch(
                        **{f"{PROPERTIES}.{REPLICATION_SOURCE_ID}": replication_source}
                    ),
                ]
            )
        )
        .source(includes=["aggregations"])
    )
    for keyword in properties:
        s.aggs.bucket(keyword, "missing", field=f"{PROPERTIES}.{keyword}.keyword")
    return s


def get_empty_entries(properties: PROPERTY_TYPE, replication_source: str) -> Response:
    return create_empty_entries_search(properties, replication_source).execute()


def api_ready_output(raw_input: dict) -> list[dict]:
    output = []
    for key, data in raw_input.items():
        data |= {"metadatum": key}
        output.append(data)
    return output


def missing_fields_ratio(total_count: int, value: dict):
    return round((1 - value["doc_count"] / total_count) * 100, 2)


def missing_fields(value: dict, total_count: int, replication_source: str) -> dict:
    return {replication_source: missing_fields_ratio(total_count, value)}


async def quality_matrix() -> list[dict]:
    properties = get_properties()
    output = {k: {} for k in properties}
    for replication_source, total_count in all_sources().items():
        response = get_empty_entries(properties, replication_source)
        for key, value in response.aggregations.to_dict().items():
            output[key] |= missing_fields(value, total_count, replication_source)

    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)
