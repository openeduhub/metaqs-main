import json
from typing import List, Dict

from elasticsearch_dsl import AttrDict
from elasticsearch_dsl.response import Response, Hit

from app.core.config import ELASTIC_MAX_SIZE
from app.core.logging import logger
from app.crud.elastic import base_filter
from app.elastic import Search, qbool, qexists, aterms

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
                result.update({replication_source: {"entries": 0}})
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


async def get_quality_matrix():
    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))
    s.aggs.bucket("property_count", aterms(qfield="properties"))

    second_response: Response = s.source(includes=[f'{PROPERTIES}.*'], excludes=[])[:ELASTIC_MAX_SIZE].execute()
    logger.info(f"second_response: {second_response}")
    with open("/tmp/test_file1", "a+") as outfile:
        json.dump([hit.to_dict() for hit in second_response.hits], outfile)

    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))
    s.aggs.bucket("entry_count", aterms(qfield="ccm:replicationsource"))

    second_response: Response = s.source(includes=[f'{PROPERTIES}.*'], excludes=[])[:ELASTIC_MAX_SIZE].execute()
    logger.info(f"second_response: {second_response}")
    with open("/tmp/test_file2", "a+") as outfile:
        json.dump([hit.to_dict() for hit in second_response.hits], outfile)

    # direct query
    search_param = {}
    response = Search().search(index="some_index", body=search_param)
    # test aggregate
    if second_response.success():
        return extract_replication_source(second_response.hits)

    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))

    response: Response = s.source(includes=[f'{PROPERTIES}.*'], excludes=[])[:ELASTIC_MAX_SIZE].execute()

    element_counter = 0
    for hit in s.source(includes=[f'{PROPERTIES}.*'], excludes=[]).scan():
        element_counter += 1

    logger.info(f"element_counter: {element_counter}")

    # test aggregate
    if response.success():
        return extract_replication_source(response.hits)
