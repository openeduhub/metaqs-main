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
    MissingAttributeFilter,
    base_filter,
    get_many_base_query,
)
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qterm
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.fields import ElasticField, ElasticFieldType
from app.elastic.search import Search
from app.elastic.utils import handle_text_field
from app.models import ElasticResourceAttribute


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


def query_many(resource_type: ResourceType, ancestor_id: UUID = None) -> Query:
    qfilter = [*base_filter, *type_filter[resource_type]]
    if ancestor_id:
        if resource_type is ResourceType.COLLECTION:
            qfilter.append(qterm(qfield=CollectionAttribute.PATH, value=ancestor_id))
        elif resource_type is ResourceType.MATERIAL:
            qfilter.append(
                qterm(
                    qfield=LearningMaterialAttribute.COLLECTION_PATH, value=ancestor_id
                )
            )

    return qbool(filter=qfilter)


def query_materials(ancestor_id: UUID = None) -> Query:
    return query_many(ResourceType.MATERIAL, ancestor_id=ancestor_id)


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


async def material_counts_by_descendant(
    ancestor_id: UUID,
) -> DescendantCollectionsMaterialsCounts:
    s = Search().query(query_materials(ancestor_id=ancestor_id))
    s.aggs.bucket("grouped_by_collection", agg_materials_by_collection()).pipeline(
        "sorted_by_count",
        abucketsort(sort=[{"_count": {"order": "asc"}}]),
    )

    response: Response = s[:0].execute()

    if response.success():
        return DescendantCollectionsMaterialsCounts.parse_elastic_response(response)


class _CollectionAttribute(ElasticField):
    TITLE = ("properties.cm:title", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", ElasticFieldType.TEXT)
    PATH = ("path", ElasticFieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)


CollectionAttribute = ElasticField(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)

_COLLECTION = TypeVar("_COLLECTION")


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


async def get_many_descendants(
    ancestor_id: Optional[UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
    source_fields: Optional[set[CollectionAttribute]] = None,
) -> list[Collection]:
    query_dict = get_many_base_query(
        resource_type=ResourceType.COLLECTION,
        ancestor_id=ancestor_id,
    )
    if missing_attr_filter:
        query_dict = missing_attr_filter.__call__(query_dict=query_dict)
    s = Search().query(qbool(**query_dict))

    search = s.source([source.path for source in source_fields])[:max_hits]

    response = search.execute()

    if response.success():
        return [Collection.parse_elastic_hit(hit) for hit in response]
