from elasticsearch_dsl.response import Response

from app.crud.elastic import base_filter
from app.elastic import Search, qbool, qexists


async def get_quality_matrix():
    qfilter = [*base_filter, qexists("ccm:replicationsource")]
    s = Search().query(qbool(filter=qfilter))

    response: Response = s.source()[:1].execute()

    if response.success():
        return response.hits
