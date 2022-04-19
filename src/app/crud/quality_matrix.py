import json
import time
from typing import List, Dict

from elasticsearch_dsl import AttrDict, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.response import Response, Hit

from app.core.config import ELASTIC_MAX_SIZE
from app.core.logging import logger
from app.crud.elastic import base_filter, base_match_filter
from app.elastic import Search, qbool, qexists, aterms, qmatch
from app.models.elastic import ElasticResourceAttribute

REPLICATION_SOURCE = "ccm:replicationsource"
PROPERTIES = "properties"


def extract_replication_source(data: List[AttrDict]) -> Dict:
    result = {}
    # TODO: Rewrite functional
    for attribute_element in data:
        element = attribute_element.to_dict()
        # logger.debug(f"Evaluating element: {element}")

        if REPLICATION_SOURCE in element[PROPERTIES].keys():
            replication_source = element[PROPERTIES][REPLICATION_SOURCE]
            if replication_source not in result.keys():
                result |= {replication_source: {"entries": 0}}
            result[replication_source]["entries"] += 1
            for key, content in element[PROPERTIES].items():
                content_value = 0
                # TODO differentiate depending on type, e.g., string or list
                if content != "":
                    content_value = 1

                if key not in result[replication_source].keys():
                    result[replication_source].update({key: content_value})
                else:
                    result[replication_source][key] = content_value + result[replication_source][key]
                # logger.debug(content, content_value, result[replication_source][key])
    return result
    # TODO: Potentially some sources do not have all properties


def write_to_json(filename: str, response):
    logger.info(f"filename: {filename}")
    with open(f"/tmp/{filename}.json", "a+") as outfile:
        json.dump([hit.to_dict() for hit in response.hits], outfile)


async def get_sources():
    time1 = time.perf_counter()
    print("get_sources")
    non_empty_entries = {
        "aggs": {
            "uniquefields": {
                "terms": {
                    "field": "properties.ccm:replicationsource.keyword"
                }
            }
        },
        "_source": ["properties.ccm:replicationsource"
                    ]
    }
    s = Search().from_dict(non_empty_entries)
    time3 = time.perf_counter()
    print(s.to_dict())
    response: Response = s.execute(ignore_cache=True)
    time4 = time.perf_counter()
    print(f"Timing: {time1}, {time3}, {time4}")
    print(f"Response: {response}")
    print(f"Response: {[hit.to_dict() for hit in response.hits]}")
    # write_to_json("sources", response)
    return {}


async def get_quality_matrix():
    sources = ["learning_apps_spider", "geogebra_spider", "youtube_spider", "bpb_spider", "br_rss_spider",
               "rpi_virtuell_spider", "tutory_spider", "oai_sodis_spider", "zum_spider", "memucho_spider"]
    fields_to_check = ["cm:creator"]
    output = {}

    PERMISSION_READ = "permissions.Read"
    EDU_METADATASET = "properties.cm:edu_metadataset"
    PROTOCOL = "nodeRef.storeRef.protocol"
    for source in sources:
        output.update({source: {}})
        for field in fields_to_check:
            s = Search().query("match", qbool(**{
                f"{PROPERTIES}.{REPLICATION_SOURCE}": source, PERMISSION_READ: "GROUP_EVERYONE",
                EDU_METADATASET: "mds_oeh", PROTOCOL: "workspace"})).exclude(
                "match", **{f"{PROPERTIES}.{field}": ""})
            print(f"Not empty counting: {s.to_dict()}")
            count: int = s.source().count()

            s = Search().query("match", qbool(**{
                f"{PROPERTIES}.{REPLICATION_SOURCE}": source, PERMISSION_READ: "GROUP_EVERYONE",
                EDU_METADATASET: "mds_oeh", PROTOCOL: "workspace"}))
            print(f"Total counting: {s.to_dict()}")
            total_count: int = s.source().count()

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
            dict_counting: int = s.source().count()
            output[source].update({f"{PROPERTIES}.{field}": {"not_empty": count, "total_count": total_count,
                                                             "dict_counting": dict_counting}})

    return output
