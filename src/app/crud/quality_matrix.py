import json
from typing import List, Dict

from elasticsearch_dsl import AttrDict, Q
from elasticsearch_dsl.aggs import Agg
from elasticsearch_dsl.response import Response, Hit

from app.core.config import ELASTIC_MAX_SIZE
from app.core.logging import logger
from app.crud.elastic import base_filter
from app.elastic import Search, qbool, qexists, aterms, qmatch

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
    s = Search().filter("bool", must=base_filter)
    s.aggs.bucket("uniquefields", "terms", field="properties.ccm:replicationsource.keyword")
    print(s.to_dict())
    response: Response = s[:ELASTIC_MAX_SIZE].execute()
    write_to_json("sources", response)


async def get_quality_matrix():
    sources = ["learning_apps_spider", "geogebra_spider", "youtube_spider", "bpb_spider", "br_rss_spider",
               "rpi_virtuell_spider", "tutory_spider", "oai_sodis_spider", "zum_spider", "memucho_spider"]
    fields_to_check = ["cm:creator"]
    output = {}

    for source in sources:
        output.update({source: {}})
        for field in fields_to_check:
            match_for_source = qmatch(**{
                REPLICATION_SOURCE: source})
            match_for_empty_entry = qmatch(**{f"{PROPERTIES}.{field}": ""})

            s = Search().filter("bool", must=[match_for_source, *base_filter], must_not=[match_for_empty_entry])
            print(f"First counting: {s.to_dict()}")
            count: int = s.source().count()

            s = Search().filter("bool", must=[match_for_source, *base_filter])
            print(f"Second counting: {s.to_dict()}")
            total_count: int = s.source().count()
            output[source].update({f"{PROPERTIES}.{field}": {"not_empty": count, "total_count": total_count}})

    """
    {'query': {'bool': {'filter': [{'bool': {'must': [{'term': {'permissions.Read.keyword': 'GROUP_EVERYONE'}}, {'term': {'properties.cm:edu_metadataset.keyword': 'mds_oeh'}}, {'term': {'nodeRef.storeRef.protocol': 'workspace'}}]}}]}}, 'aggs': {'uniquefields': {'terms': {'field': 'properties.ccm:replicationsource.keyword'}}}}
metaqs-fastapi  | First counting: {'query': {'bool': {'filter': [{'bool': {'must': [{'match': {'ccm:replicationsource': 'learning_apps_spider'}}, {'term': {'permissions.Read.keyword': 'GROUP_EVERYONE'}}, {'term': {'properties.cm:edu_metadataset.keyword': 'mds_oeh'}}, {'term': {'nodeRef.storeRef.protocol': 'workspace'}}], 'must_not': [{'match': {'properties.cm:creator': ''}}]}}]}}}
metaqs-fastapi  | Second counting: {'query': {'bool': {'filter': [{'bool': {'must': [{'match': {'ccm:replicationsource': 'learning_apps_spider'}}, {'term': {'permissions.Read.keyword': 'GROUP_EVERYONE'}}, {'term': {'properties.cm:edu_metadataset.keyword': 'mds_oeh'}}, {'term': {'nodeRef.storeRef.protocol': 'workspace'}}]}}]}}}

    """
    return output
