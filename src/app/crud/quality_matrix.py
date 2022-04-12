from elasticsearch_dsl.response import Response

from app.crud.elastic import base_filter
from app.elastic import Search, qbool, qexists

REPLICATION_SOURCE = "ccm:replicationsource"
PROPERTIES = "properties"


def extract_replication_source(data):
    result = {}
    # TODO: Rewrite functional
    for element in data["hits"]:
        if REPLICATION_SOURCE in element["_source"][PROPERTIES].keys():
            replication_source = element["_source"][PROPERTIES][REPLICATION_SOURCE]
            print(replication_source)
            if replication_source not in result.keys():
                result.update({replication_source: {"entries": 0}})
            result[replication_source]["entries"] += 1
            for key, content in element["_source"][PROPERTIES].items():
                content_value = 0
                # TODO differentiate depending on type, e.g., string or list
                if content != "":
                    content_value = 1

                if key not in result[replication_source].keys():
                    result[replication_source].update({key: content_value})
                else:
                    result[replication_source][key] = content_value + result[replication_source][key]
                print(content, content_value, result[replication_source][key])
    print(result)
    return result
    # TODO: Potentially some sources do not have all properties


async def get_quality_matrix():
    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))

    response: Response = s.source(includes=[f'{PROPERTIES}.*'], excludes=[])[:100].execute()

    if response.success():
        return extract_replication_source(response.hits)
