import json

from elasticsearch_dsl import AttrDict, Q
from elasticsearch_dsl.response import Response
from app.core.logging import logger
from app.crud.elastic import base_match_filter
from app.elastic import Search, qmatch, qbool

REPLICATION_SOURCE = "ccm:replicationsource"
PROPERTIES = "properties"

PERMISSION_READ = "permissions.Read"
EDU_METADATASET = "properties.cm:edu_metadataset"
PROTOCOL = "nodeRef.storeRef.protocol"


def write_to_json(filename: str, response):
    logger.info(f"filename: {filename}")
    with open(f"/tmp/{filename}.json", "a+") as outfile:
        json.dump([hit.to_dict() for hit in response.hits], outfile)


def get_sources() -> dict[str: int]:
    aggregation_name = "unique_sources"
    main_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "permissions.Read": "GROUP_EVERYONE"
                        }
                    },
                    {
                        "match": {
                            "properties.cm:edu_metadataset": "mds_oeh"
                        }
                    },
                    {
                        "match": {
                            "nodeRef.storeRef.protocol": "workspace"
                        }
                    }
                ]
            }
        }
    }
    s = Search().from_dict(main_query)
    s.aggs.bucket(aggregation_name, "terms", field="properties.ccm:replicationsource.keyword")
    response: Response = s.execute()
    return {entry["key"]: entry["doc_count"] for entry in response.aggregations.to_dict()[aggregation_name]["buckets"]}


def extract_properties(hits: list[AttrDict]) -> list:
    return hits[0].to_dict()[PROPERTIES].keys()


def get_properties():
    property_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "permissions.Read": "GROUP_EVERYONE"
                        }
                    },
                    {
                        "match": {
                            "properties.cm:edu_metadataset": "mds_oeh"
                        }
                    },
                    {
                        "match": {
                            "nodeRef.storeRef.protocol": "workspace"
                        }
                    }
                ]
            }
        },
        "_source": [
            "properties"
        ]
    }
    s = Search().from_dict(property_query)
    response = s.execute()
    return extract_properties(response.hits)


def create_empty_entries_search(field, source):
    s = Search().query(qbool(must=[
        qmatch(**{f"{PROPERTIES}.{REPLICATION_SOURCE}": source}),
        qmatch(**{f"{PROPERTIES}.{field}": ""})
    ]
    ))
    for entry in base_match_filter:
        s = s.query(entry)
    return s


def get_empty_entries(field, source):
    s = create_empty_entries_search(field, source)
    logger.debug(f"From dict empty_entries: {s.to_dict()}")
    empty: int = s.source().count()
    return empty


def get_non_empty_entries(field, source):
    non_empty_entries = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "properties.ccm:replicationsource": source
                        }
                    }
                ],
                "must_not": [
                    {
                        "match": {
                            f"properties.{field}": ""
                        }
                    }
                ]
            }
        }
    }
    s = Search().from_dict(non_empty_entries)
    logger.debug(f"From dict counting: {s.to_dict()}")
    for entry in base_match_filter:
        s = s.query(entry)
    count: int = s.source().count()
    return count


async def get_quality_matrix():
    output = {}

    for source, total_count in get_sources().items():
        output.update({source: {}})
        for field in get_properties():
            count = get_non_empty_entries(field, source)

            empty = get_empty_entries(field, source)
            output[source].update(
                {f"{PROPERTIES}.{field}": {"empty": empty, "not_empty": count, "total_count": total_count}})

    return output
