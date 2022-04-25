import json

from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response

from app.core.constants import PROPERTIES, REPLICATION_SOURCE
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
        aggregation_name, "terms", field=f"{PROPERTIES}.{REPLICATION_SOURCE}.keyword"
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
    return hits[0].to_dict()[PROPERTIES].keys()


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
                    qmatch(**{f"{PROPERTIES}.{REPLICATION_SOURCE}": source}),
                    qmatch(**{f"{PROPERTIES}.{field}": ""}),
                ]
            )
        )
    )


def get_empty_entries(field, source):
    return create_empty_entries_search(field, source).source().count()


def create_non_empty_entries_search(field, source):
    return add_base_match_filters(
        Search().query(
            qbool(
                must=[
                    qmatch(**{f"{PROPERTIES}.{REPLICATION_SOURCE}": source}),
                ],
                must_not=[qmatch(**{f"{PROPERTIES}.{field}": ""})],
            )
        )
    )


def get_non_empty_entries(field, source):
    s = create_non_empty_entries_search(field, source)
    logger.debug(f"From dict counting: {s.to_dict()}")
    count: int = s.source().count()
    return count


async def quality_matrix():
    output = {}

    for source, total_count in all_sources().items():
        output |= {source: {}}
        for field in get_properties():
            count = get_non_empty_entries(field, source)

            empty = get_empty_entries(field, source)
            output[source] |= {
                f"{PROPERTIES}.{field}": {
                    "empty": empty,
                    "not_empty": count,
                    "total_count": total_count,
                }
            }

    logger.debug(f"Quality matrix output:\n{output}")
    return output
