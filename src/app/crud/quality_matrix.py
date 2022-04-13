import json
from typing import List, Dict

from elasticsearch_dsl import AttrDict, Q
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

def write_to_json(filename: str, response):
    logger.info(f"filename: {response}")
    with open(f"/tmp/{filename}.json", "a+") as outfile:
        json.dump([hit.to_dict() for hit in response.hits], outfile)


async def get_quality_matrix():
    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))
    s.aggs.bucket("property_count", aterms(qfield="properties"))

    second_response: Response = s.source(includes=[f'{PROPERTIES}.*'], excludes=[])[:ELASTIC_MAX_SIZE].execute()
    write_to_json("test_file1", second_response)

    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))
    s.aggs.bucket("entry_count", aterms(qfield="ccm:replicationsource"))

    second_response: Response = s.source(includes=[f'{PROPERTIES}.*'], excludes=[])[:ELASTIC_MAX_SIZE].execute()
    write_to_json("test_file2", second_response)

    query = Q("multi_match", query="test_multiple", fields=["cm:creator", "ccm:replicationsource"])
    second_response = Search().query(query)[:ELASTIC_MAX_SIZE].execute()
    write_to_json("test_file3", second_response)

    query = Q("match", title='ccm:replicationsource') & Q("match", title='')
    second_response = Search().query(query)[:ELASTIC_MAX_SIZE].execute()
    write_to_json("test_file4", second_response)

    # original query
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
