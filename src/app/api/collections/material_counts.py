from __future__ import annotations

import uuid
from typing import Optional, Type, TypeVar

from elasticsearch_dsl.aggs import A, Agg
from elasticsearch_dsl.response import Response
from glom import Coalesce, Iter, glom
from pydantic import BaseModel, Extra

from app.api.collections.models import MissingMaterials
from app.api.collections.utils import all_source_fields, map_elastic_response_to_model
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import ElasticResourceAttribute, ResponseModel
from app.elastic.dsl import aterms, qbool, qmatch
from app.elastic.elastic import ResourceType
from app.elastic.search import Search

_COLLECTION = TypeVar("_COLLECTION")


class CollectionMaterialsCount(ResponseModel):
    node_id: uuid.UUID
    title: str
    materials_count: int


T = TypeVar("T")


# TODO: Refactor
class DescendantCollectionsMaterialsCounts(BaseModel):
    results: list[CollectionMaterialsCount]

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        extra = Extra.forbid

    @classmethod
    def parse_elastic_response(
        cls: Type[T],
        response: Response,
    ) -> T:
        results = glom(
            response,
            (
                "aggregations.grouped_by_collection.buckets",
                [{"node_id": "key.noderef_id", "materials_count": "doc_count"}],
            ),
        )
        return cls.construct(
            results=[
                CollectionMaterialsCount.construct(**record) for record in results
            ],
        )


def agg_materials_by_collection(size: int = 65536) -> Agg:
    return A(
        "composite",
        sources=[
            {
                "noderef_id": aterms(
                    qfield=ElasticResourceAttribute.COLLECTION_NODEREF_ID
                )
            }
        ],
        size=size,
    )


def material_counts_by_children(
    node_id: uuid.UUID,
) -> DescendantCollectionsMaterialsCounts:
    search = material_counts_search(node_id)
    response: Response = search.execute()

    if response.success():
        return DescendantCollectionsMaterialsCounts.parse_elastic_response(response)


def material_counts_search(node_id: uuid.UUID):
    s = (
        Search()
        .base_filters()
        .node_filter(resource_type=ResourceType.MATERIAL, node_id=node_id)
    )
    s.aggs.bucket("grouped_by_collection", agg_materials_by_collection()).pipeline(
        "sorted_by_count",
        A("bucket_sort", sort=[{"_count": {"order": "asc"}}]),
    )
    return s


material_counts_spec = {
    "title": Coalesce(ElasticResourceAttribute.COLLECTION_TITLE.path, default=None),
    "keywords": (
        Coalesce(ElasticResourceAttribute.KEYWORDS.path, default=[]),
        Iter().all(),
    ),
    "description": Coalesce(
        ElasticResourceAttribute.COLLECTION_DESCRIPTION.path, default=None
    ),
    "path": (
        Coalesce(ElasticResourceAttribute.PATH.path, default=[]),
        Iter().all(),
    ),
    "parent_id": Coalesce(ElasticResourceAttribute.PARENT_ID.path, default=None),
    "node_id": ElasticResourceAttribute.NODE_ID.path,
    "type": Coalesce(ElasticResourceAttribute.TYPE.path, default=None),
    "name": Coalesce(ElasticResourceAttribute.NAME.path, default=None),
    "children": Coalesce("", default=[]),  # workaround to map easier to pydantic model
}


def descendants_search(node_id: uuid.UUID, max_hits: int):
    query = {
        "minimum_should_match": 1,
        "should": [
            qmatch(**{"path": node_id}),
            qmatch(**{"nodeRef.id": node_id}),
        ],
    }
    return (
        Search()
        .base_filters()
        .query(qbool(**query))
        .type_filter(ResourceType.COLLECTION)
        .source(includes=[source.path for source in all_source_fields])[:max_hits]
    )


def get_children(
    node_id: Optional[uuid.UUID] = None,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[MissingMaterials]:
    search = descendants_search(node_id, max_hits)

    response = search.execute()

    if response.success():
        return map_elastic_response_to_model(
            response, material_counts_spec, MissingMaterials
        )


async def get_material_count_tree(node_id: uuid.UUID) -> list[CollectionMaterialsCount]:
    """

    :param node_id:
    :return:
    """

    # TODO: Refactor get_children, it creates a lot of false hits, i.e., too many collections without materials
    children = get_children(node_id=node_id)
    materials_counts = material_counts_by_children(
        node_id=node_id,
    )
    children = {collection.node_id: collection.title for collection in children}
    counts = []
    for record in materials_counts.results:
        try:
            # TODO: Check why this type wrapping is currently required!
            title = children.pop(uuid.UUID(record.node_id))
        except KeyError:
            continue

        counts.append(
            CollectionMaterialsCount(
                node_id=record.node_id,
                title=title,
                materials_count=record.materials_count,
            )
        )
    counts = [
        *[
            CollectionMaterialsCount(
                node_id=node_id,
                title=title,
                materials_count=0,
            )
            for (node_id, title) in children.items()
        ],
        *counts,
    ]
    return counts
