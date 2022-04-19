import json
import time
from typing import List, Dict

from elasticsearch import Elasticsearch
from elasticsearch_dsl import AttrDict, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.response import Response, Hit

from app.core.config import ELASTIC_MAX_SIZE, ELASTIC_INDEX
from app.core.logging import logger
from app.crud.elastic import base_filter, base_match_filter
from app.elastic import Search, qbool, qexists, aterms, qmatch
from app.models.elastic import ElasticResourceAttribute

REPLICATION_SOURCE = "ccm:replicationsource"
PROPERTIES = "properties"


def write_to_json(filename: str, response):
    logger.info(f"filename: {filename}")
    with open(f"/tmp/{filename}.json", "a+") as outfile:
        json.dump([hit.to_dict() for hit in response.hits], outfile)


async def get_sources() -> list:
    filename = "sources"
    print(f"get_{filename}")
    s = Search()
    s.aggs.bucket("uniquefields", "terms", field="properties.ccm:replicationsource.keyword")
    print(f"get_{filename}: {s.to_dict()}")
    response: Response = s.execute()

    with open(f"/tmp/{filename}_raw.json", "a+") as outfile:
        json.dump(response.to_dict(), outfile)
    entries = [entry["key"] for entry in response.aggregations.to_dict()["uniquefields"]["buckets"]]
    with open(f"/tmp/{filename}.json", "a+") as outfile:
        json.dump({filename: entries}, outfile)
    return entries


def extract_properties(hits: list[AttrDict]) -> list:
    with open(f"/tmp/extract_properties_raw.json", "a+") as outfile:
        for hit in hits:
            print(f"extract_properties: {hit}")
            if hit.to_dict():
                json.dump(hit.to_dict(), outfile)
                return hit.to_dict()[PROPERTIES].keys()
    return ["cm:creator", "cm:content", "cm:contentPropertyName", "cm:created", "cm:isContentIndexed",
            "cm:isIndexed", "cm:modified", "cm:modifie", "cm:name", "cm:thumbnailName", "cm:description"]


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
    print(f"Get properties: {s.to_dict()}")
    response = s.execute()
    print(f"Response {response}")
    print(f"Hits {[hit.to_dict() for hit in response.hits]}")
    return extract_properties(response.hits)


async def get_quality_matrix():
    sources = ["learning_apps_spider", "geogebra_spider", "youtube_spider", "bpb_spider", "br_rss_spider",
               "rpi_virtuell_spider", "tutory_spider", "oai_sodis_spider", "zum_spider", "memucho_spider"]
    output = {}

    PERMISSION_READ = "permissions.Read"
    EDU_METADATASET = "properties.cm:edu_metadataset"
    PROTOCOL = "nodeRef.storeRef.protocol"
    for source in sources:
        output.update({source: {}})
        for field in get_properties():
            non_empty_entries = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "properties.ccm:replicationsource": source
                                }
                            },
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
                        ],
                        "must_not": [
                            {
                                "match": {
                                    "properties.cm:creator": ""
                                }
                            }
                        ]
                    }
                }
            }
            s = Search().from_dict(non_empty_entries)
            print(f"From dict counting: {s.to_dict()}")
            count: int = s.source().count()

            all_entries = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "properties.ccm:replicationsource": source
                                }
                            },
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
                        ],
                    }
                }
            }
            s = Search().from_dict(all_entries)
            print(f"From dict all_entries: {s.to_dict()}")
            total_count: int = s.source().count()

            empty_entries = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "properties.ccm:replicationsource": "learning_apps_spider"
                                }
                            },
                            {
                                "match": {
                                    "properties.cm:creator": ""
                                }
                            },
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
            s = Search().from_dict(empty_entries)
            print(f"From dict empty_entries: {s.to_dict()}")
            empty: int = s.source().count()
            output[source].update(
                {f"{PROPERTIES}.{field}": {"empty": empty, "not_empty": count, "total_count": total_count}})

    return output
