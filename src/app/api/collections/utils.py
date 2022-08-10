from typing import TypeVar, Type

from elasticsearch_dsl.response import Response
from glom import glom

from app.api.collections.models import CollectionNode, MissingMaterials
from app.core.models import ElasticResourceAttribute

T = TypeVar("T", CollectionNode, MissingMaterials)


def map_elastic_response_to_model(
    response: Response, specs: dict, model: Type[T]
) -> list[T]:
    return [model(**glom(hit.to_dict(), specs)) for hit in response]


all_source_fields: list = [
    ElasticResourceAttribute.NODE_ID,
    ElasticResourceAttribute.TYPE,
    ElasticResourceAttribute.NAME,
    ElasticResourceAttribute.COLLECTION_TITLE,
    ElasticResourceAttribute.KEYWORDS,
    ElasticResourceAttribute.COLLECTION_DESCRIPTION,
    ElasticResourceAttribute.PATH,
    ElasticResourceAttribute.PARENT_ID,
]
