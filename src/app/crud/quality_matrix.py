from elasticsearch_dsl.response import Response

from app.crud.elastic import base_filter, replication_source_filter
from app.elastic import Search, qbool


async def get_quality_matrix():
    s = Search().query(qbool(filter=base_filter))

    response: Response = s.source()[:5].execute()

    if response.success():
        return response
