from elasticsearch_dsl.response import Response

from app.crud.elastic import base_filter
from app.elastic import Search, qbool, qexists


async def get_quality_matrix():
    qfilter = [*base_filter]
    s = Search().query(qbool(filter=qfilter))

    response: Response = s.source(includes=['_source.properties.*'], excludes=[])[:100].execute()

    if response.success():
        return response.hits
