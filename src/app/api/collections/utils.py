from typing import Generic, TypeVar

from elasticsearch_dsl.response import Response
from glom import glom

from app.api.collections.models import CollectionNode, MissingMaterials

T = TypeVar("T", CollectionNode, MissingMaterials)


def map_elastic_response_to_model(
    response: Response, specs: dict, model: Generic[T]
) -> list[T]:
    collections = []
    for hit in response:
        parsed_entry = glom(hit.to_dict(), specs)
        if parsed_entry["title"] is not None:
            collections.append(model(**parsed_entry))
    return collections
