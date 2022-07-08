import uuid
from itertools import chain
from typing import Optional, Type, TypeVar, Union
from uuid import UUID

from elasticsearch_dsl.aggs import A, Agg
from elasticsearch_dsl.query import Query
from elasticsearch_dsl.response import Response
from glom import Coalesce, Iter, glom
from pydantic import BaseModel, Extra

from app.api.collections.missing_materials import (
    ElasticResource,
    EmptyStrToNone,
    LearningMaterialAttribute,
)
from app.api.collections.utils import all_source_fields
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import ResourceType, query_materials, type_filter
from app.elastic.fields import ElasticField, ElasticFieldType
from app.elastic.search import Search
from app.elastic.utils import handle_text_field
from app.models import ElasticResourceAttribute


class _CollectionAttribute(ElasticField):
    TITLE = ("properties.cm:title", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", ElasticFieldType.TEXT)
    PATH = ("path", ElasticFieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)
    NODE_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)


_COLLECTION = TypeVar("_COLLECTION")
# TODO Remove duplicate
CollectionAttribute = ElasticField(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass


class CollectionMaterialsCount(ResponseModel):
    noderef_id: UUID
    title: str
    materials_count: int


_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS = TypeVar(
    "_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS"
)


# TODO: Refactor
class DescendantCollectionsMaterialsCounts(BaseModel):
    results: list[CollectionMaterialsCount]

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        extra = Extra.forbid

    @classmethod
    def parse_elastic_response(
        cls: Type[_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS],
        response: Response,
    ) -> _DESCENDANT_COLLECTIONS_MATERIALS_COUNTS:
        results = glom(
            response,
            (
                "aggregations.grouped_by_collection.buckets",
                [{"noderef_id": "key.noderef_id", "materials_count": "doc_count"}],
            ),
        )
        return cls.construct(
            results=[
                CollectionMaterialsCount.construct(**record) for record in results
            ],
        )


def aterms(qfield: Union[ElasticField, str], **kwargs) -> Agg:
    kwargs["field"] = handle_text_field(qfield)
    return A("terms", **kwargs)


def acomposite(sources: list[Union[Query, dict]], **kwargs) -> Agg:
    return A("composite", sources=sources, **kwargs)


def agg_materials_by_collection(size: int = 65536) -> Agg:
    return acomposite(
        sources=[
            {
                "noderef_id": aterms(
                    qfield=LearningMaterialAttribute.COLLECTION_NODEREF_ID
                )
            }
        ],
        size=size,
    )


def abucketsort(sort: list[Union[Query, dict]], **kwargs) -> Agg:
    return A("bucket_sort", sort=sort, **kwargs)


def material_counts_by_descendant(
    node_id: uuid.UUID,
) -> DescendantCollectionsMaterialsCounts:
    search = material_counts_search(node_id)
    response: Response = search.execute()

    if response.success():
        return DescendantCollectionsMaterialsCounts.parse_elastic_response(response)


def material_counts_search(node_id: uuid.UUID):
    s = Search().base_filters().query(query_materials(node_id=node_id))
    s.aggs.bucket("grouped_by_collection", agg_materials_by_collection()).pipeline(
        "sorted_by_count",
        abucketsort(sort=[{"_count": {"order": "asc"}}]),
    )
    return s


class CollectionBase(ElasticResource):
    title: Optional[EmptyStrToNone] = None
    keywords: Optional[list[str]] = None
    description: Optional[EmptyStrToNone] = None
    path: Optional[list[UUID]] = None
    parent_id: Optional[UUID] = None

    source_fields = {
        CollectionAttribute.NODEREF_ID,
        CollectionAttribute.TYPE,
        CollectionAttribute.NAME,
        CollectionAttribute.TITLE,
        CollectionAttribute.KEYWORDS,
        CollectionAttribute.DESCRIPTION,
        CollectionAttribute.PATH,
        CollectionAttribute.PARENT_ID,
    }

    @classmethod
    def parse_elastic_hit_to_dict(
        cls: Type[_COLLECTION],
        hit: dict,
    ) -> dict:
        spec = {
            "title": Coalesce(CollectionAttribute.TITLE.path, default=None),
            "keywords": (
                Coalesce(CollectionAttribute.KEYWORDS.path, default=[]),
                Iter().all(),
            ),
            "description": Coalesce(CollectionAttribute.DESCRIPTION.path, default=None),
            "path": (
                Coalesce(CollectionAttribute.PATH.path, default=[]),
                Iter().all(),
            ),
            "parent_id": Coalesce(CollectionAttribute.PARENT_ID.path, default=None),
        }
        return {
            **super(CollectionBase, cls).parse_elastic_hit_to_dict(hit),
            **glom(hit, spec),
        }

    @classmethod
    def parse_elastic_hit(
        cls: Type[_COLLECTION],
        hit: dict,
    ) -> _COLLECTION:
        collection = cls.construct(**cls.parse_elastic_hit_to_dict(hit))
        try:
            collection.parent_id = collection.path[-1]
        except IndexError:
            pass
        return collection


class Collection(ResponseModel, CollectionBase):
    pass


def descendants_search(node_id: uuid.UUID, max_hits):
    query = {
        "filter": [*type_filter[ResourceType.COLLECTION]],
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
        .source(includes=[source.path for source in all_source_fields])[:max_hits]
    )


def get_many_descendants(
    node_id: Optional[UUID] = None,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[Collection]:
    search = descendants_search(node_id, max_hits)

    response = search.execute()

    if response.success():
        return [Collection.parse_elastic_hit(hit) for hit in response]


async def get_material_count_tree(node_id) -> list[CollectionMaterialsCount]:
    """
    TODO: Refactor this function, it is very unclear to me

    :param node_id:
    :return:
    """
    descendant_collections = get_many_descendants(node_id=node_id)
    materials_counts = material_counts_by_descendant(
        node_id=node_id,
    )
    descendant_collections = {
        collection.noderef_id: collection.title for collection in descendant_collections
    }
    stats = []
    for record in materials_counts.results:
        try:
            title = descendant_collections.pop(record.noderef_id)
        except KeyError:
            continue

        stats.append(
            CollectionMaterialsCount(
                noderef_id=record.noderef_id,
                title=title,
                materials_count=record.materials_count,
            )
        )
    stats = [
        *[
            CollectionMaterialsCount(
                noderef_id=noderef_id,
                title=title,
                materials_count=0,
            )
            for (noderef_id, title) in descendant_collections.items()
        ],
        *stats,
    ]
    return stats
