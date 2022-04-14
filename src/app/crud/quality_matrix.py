import json
from typing import List, Dict

from elasticsearch_dsl import AttrDict, Q
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
    # original query
    qfilter = [*base_filter]
    sources = ["learning_apps_spider"]
    fields_to_check = ["properties.cm:creator"]
    output = {}

    for source in sources:
        output.update({source: {}})
        for field in fields_to_check:
            match_for_source = qmatch(**{
                "properties.ccm:replicationsource": source})
            match_for_empty_entry = qmatch(**{field: ""})
            s = Search().filter("bool", must=[match_for_source, *qfilter], must_not=[match_for_empty_entry])
            response: Response = s.source().execute()
            write_to_json(f"executed_{source}_{field}", response)
            count: int = s.source().count()

            s = Search().filter("bool", must=[match_for_source, *qfilter])
            total_count: int = s.source().count()
            output[source].update({field: {"not_empty": count, "total_count": total_count}})
    # test aggregate
    with open(f"/tmp/{output}.json", "a+") as outfile:
        json.dump(output, outfile)
    return output
