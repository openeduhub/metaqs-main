from elasticsearch_dsl.response import Response

from app.core.config import PORTAL_ROOT_ID, ELASTIC_MAX_SIZE
from app.crud.elastic import query_collections, base_filter
from app.elastic import Search, qbool
from app.models.collection import Collection, CollectionAttribute
from app.models.elastic import ElasticResourceAttribute


async def get_quality_matrix():
    s = Search().query(qbool(filter=[*base_filter]))

    response: Response = s.source()[:100].execute()

    if response.success():
        return response
