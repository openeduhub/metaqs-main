import json

from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

from app.core.constants import (
    PROPERTIES,
    REPLICATION_SOURCE,
    REPLICATION_SOURCE_ID,
    TOTAL_COUNT,
)
from app.core.logging import logger
from app.crud.elastic import base_match_filter
from app.elastic import Search, qbool, qmatch


def add_base_match_filters(search: Search) -> Search:
    for entry in base_match_filter:
        search = search.query(entry)
    return search


def write_to_json(filename: str, response):
    logger.info(f"filename: {filename}")
    with open(f"/tmp/{filename}.json", "a+") as outfile:
        json.dump([hit.to_dict() for hit in response.hits], outfile)


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


def extract_properties(hits: list[AttrDict]) -> list:
    return list(hits[0].to_dict()[PROPERTIES].keys())


def create_properties_search() -> Search:
    return add_base_match_filters(Search().source([PROPERTIES]))


def get_properties():
    s = create_properties_search()
    response = s.execute()
    return extract_properties(response.hits)


def create_empty_entries_search(field, source):
    return add_base_match_filters(
        Search().query(
            qbool(
                must=[
                    qmatch(**{f"{PROPERTIES}.{REPLICATION_SOURCE_ID}": source}),
                    qmatch(**{f"{PROPERTIES}.{field}": ""}),
                ]
            )
        )
    )


def get_empty_entries(field, source):
    return create_empty_entries_search(field, source).count()


def create_non_empty_entries_search(field, source):
    return add_base_match_filters(
        Search().query(
            qbool(
                must=[
                    qmatch(**{f"{PROPERTIES}.{REPLICATION_SOURCE_ID}": source}),
                ],
                must_not=[qmatch(**{f"{PROPERTIES}.{field}": ""})],
            )
        )
    )


def api_ready_output(raw_input: dict) -> list[dict]:
    output = []
    for entry in raw_input[PROPERTIES]:
        data = {
            source: raw_input[source][entry] for source in raw_input[REPLICATION_SOURCE]
        }
        data |= {"metadatum": entry}
        output.append(data)
    return output


async def quality_matrix() -> list[dict]:
    output = {}

    properties = get_properties()
    output |= {PROPERTIES: properties, REPLICATION_SOURCE: []}
    for replication_source, total_count in all_sources().items():
        source_data = {TOTAL_COUNT: total_count}
        output[REPLICATION_SOURCE].append(replication_source)
        if total_count > 0:
            for field in properties:
                empty = get_empty_entries(field, replication_source)
                source_data |= {f"{field}": round(1 - empty / total_count, 4) * 100.0}
        output |= {replication_source: source_data}
    logger.debug(f"Quality matrix output:\n{output}")
    return api_ready_output(output)
