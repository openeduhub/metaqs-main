from itertools import chain
from typing import ClassVar, Optional, Type, TypeVar, Union
from uuid import UUID

from elasticsearch_dsl import Q
from fastapi.params import Path, Query
from glom import Coalesce, Iter, glom
from pydantic import BaseModel, Extra
from pydantic.validators import str_validator

from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qmatch, qterm
from app.elastic.elastic import (
    ResourceType,
    query_missing_material_license,
    type_filter,
)
from app.elastic.fields import ElasticField, ElasticFieldType
from app.elastic.search import Search
from app.models import _ELASTIC_RESOURCE, CollectionAttribute, ElasticResourceAttribute

_LEARNING_MATERIAL = TypeVar("_LEARNING_MATERIAL")


class _LearningMaterialAttribute(ElasticField):
    TITLE = ("properties.cclom:title", ElasticFieldType.TEXT)
    SUBJECTS = ("properties.ccm:taxonid", ElasticFieldType.TEXT)
    SUBJECTS_DE = ("i18n.de_DE.ccm:taxonid", ElasticFieldType.TEXT)
    WWW_URL = ("properties.ccm:wwwurl", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cclom:general_description", ElasticFieldType.TEXT)
    LICENSES = ("properties.ccm:commonlicense_key", ElasticFieldType.TEXT)
    COLLECTION_NODEREF_ID = ("collections.nodeRef.id", ElasticFieldType.TEXT)
    COLLECTION_PATH = ("collections.path", ElasticFieldType.TEXT)
    CONTENT_FULLTEXT = ("content.fulltext", ElasticFieldType.TEXT)
    LEARNINGRESOURCE_TYPE = (
        "properties.ccm:oeh_lrt_aggregated",
        ElasticFieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt_aggregated",
        ElasticFieldType.TEXT,
    )
    EDUENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        ElasticFieldType.TEXT,
    )
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", ElasticFieldType.TEXT)
    OBJECT_TYPE = ("properties.ccm:objecttype", ElasticFieldType.TEXT)


LearningMaterialAttribute = ElasticField(
    "LearningMaterialAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _LearningMaterialAttribute)
    ],
)


def empty_to_none(v: str) -> Optional[str]:
    if v == "":
        return None
    return v


class EmptyStrToNone(str):
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield empty_to_none


class ElasticConfig:
    allow_population_by_field_name = True
    extra = Extra.allow


class ElasticResource(BaseModel):
    noderef_id: UUID
    type: Optional[EmptyStrToNone] = None
    name: Optional[EmptyStrToNone] = None

    source_fields: ClassVar[set] = {
        ElasticResourceAttribute.NODEREF_ID,
        ElasticResourceAttribute.TYPE,
        ElasticResourceAttribute.NAME,
    }

    class Config(ElasticConfig):
        pass

    @classmethod
    def parse_elastic_hit_to_dict(
        cls: Type[_ELASTIC_RESOURCE],
        hit: dict,
    ) -> dict:
        spec = {
            "noderef_id": ElasticResourceAttribute.NODEREF_ID.path,
            "type": Coalesce(ElasticResourceAttribute.TYPE.path, default=None),
            "name": Coalesce(ElasticResourceAttribute.NAME.path, default=None),
        }
        return glom(hit, spec)

    @classmethod
    def parse_elastic_hit(
        cls: Type[_ELASTIC_RESOURCE],
        hit: dict,
    ) -> _ELASTIC_RESOURCE:
        return cls.construct(**cls.parse_elastic_hit_to_dict(hit))


class LearningMaterialBase(ElasticResource):
    title: Optional[EmptyStrToNone] = None
    keywords: Optional[list[str]] = None
    edu_context: Optional[list[str]] = None
    subjects: Optional[list[str]] = None
    www_url: Optional[str] = None
    description: Optional[EmptyStrToNone] = None
    licenses: Optional[EmptyStrToNone] = None

    source_fields: ClassVar[set] = {
        LearningMaterialAttribute.NODEREF_ID,
        LearningMaterialAttribute.TYPE,
        LearningMaterialAttribute.NAME,
        LearningMaterialAttribute.TITLE,
        LearningMaterialAttribute.KEYWORDS,
        LearningMaterialAttribute.EDU_CONTEXT,
        LearningMaterialAttribute.SUBJECTS,
        LearningMaterialAttribute.WWW_URL,
        LearningMaterialAttribute.DESCRIPTION,
        LearningMaterialAttribute.LICENSES,
    }

    @classmethod
    def parse_elastic_hit_to_dict(
        cls: Type[_LEARNING_MATERIAL],
        hit: dict,
    ) -> dict:
        spec = {
            "title": Coalesce(LearningMaterialAttribute.TITLE.path, default=None),
            "keywords": (
                Coalesce(LearningMaterialAttribute.KEYWORDS.path, default=[]),
                Iter().all(),
            ),
            "edu_context": (
                Coalesce(LearningMaterialAttribute.EDU_CONTEXT.path, default=[]),
                Iter().all(),
            ),
            "subjects": (
                Coalesce(LearningMaterialAttribute.SUBJECTS.path, default=[]),
                Iter().all(),
            ),
            "www_url": Coalesce(LearningMaterialAttribute.WWW_URL.path, default=None),
            "description": (
                Coalesce(LearningMaterialAttribute.DESCRIPTION.path, default=[]),
                (Iter().all(), "\n".join),
            ),
            "licenses": (
                Coalesce(LearningMaterialAttribute.LICENSES.path, default=[]),
                (Iter().all(), "\n".join),
            ),
        }
        return {
            **super(LearningMaterialBase, cls).parse_elastic_hit_to_dict(hit),
            **glom(hit, spec),
        }


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass


class LearningMaterial(ResponseModel, LearningMaterialBase):
    pass


LearningMaterialResponseField = ElasticField(
    "MaterialAttribute",
    [(f.name, (f.value, f.field_type)) for f in LearningMaterialAttribute],
)


def material_response_fields(
    *, response_fields: set[LearningMaterialResponseField] = Query(None)
) -> set[LearningMaterialAttribute]:
    return response_fields


MissingMaterialField = ElasticField(
    "MissingMaterialField",
    [
        (f.name, (f.value, f.field_type))
        for f in [
            LearningMaterialAttribute.NAME,
            LearningMaterialAttribute.TITLE,
            LearningMaterialAttribute.KEYWORDS,
            LearningMaterialAttribute.EDU_CONTEXT,
            LearningMaterialAttribute.SUBJECTS,
            LearningMaterialAttribute.WWW_URL,
            LearningMaterialAttribute.DESCRIPTION,
            LearningMaterialAttribute.LICENSES,
        ]
    ],
)


def qwildcard(qfield: Union[ElasticField, str], value: str) -> Query:
    if isinstance(qfield, ElasticField):
        qfield = qfield.path
    return Q("wildcard", **{qfield: {"value": value}})


class MissingAttributeFilter(BaseModel):
    attr: MissingMaterialField

    def __call__(self, query_dict: dict):
        if self.attr == LearningMaterialAttribute.LICENSES:
            query_dict["filter"].append(query_missing_material_license())
        else:
            query_dict["must_not"] = qwildcard(qfield=self.attr, value="*")

        return query_dict


def materials_filter_params(
    *, missing_attr: MissingMaterialField = Path(...)
) -> MissingAttributeFilter:
    return MissingAttributeFilter(attr=missing_attr)


base_filter = [
    qterm(qfield=ElasticResourceAttribute.PERMISSION_READ, value="GROUP_EVERYONE"),
    qterm(qfield=ElasticResourceAttribute.EDU_METADATASET, value="mds_oeh"),
    qterm(qfield=ElasticResourceAttribute.PROTOCOL, value="workspace"),
]


def get_many_base_query(
    resource_type: ResourceType,
    ancestor_id: Optional[UUID] = None,
) -> dict:
    query_dict = {"filter": [*base_filter, *type_filter[resource_type]]}

    if ancestor_id:
        prefix = "collections." if resource_type == ResourceType.MATERIAL else ""
        query_dict["should"] = [
            qmatch(**{f"{prefix}path": ancestor_id}),
            qmatch(**{f"{prefix}nodeRef.id": ancestor_id}),
        ]
        query_dict["minimum_should_match"] = 1

    return query_dict


def missing_attributes_search(
    noderef_id: UUID, missing_attribute: str, max_hits: int
) -> Search:
    query = {
        "filter": [*type_filter[ResourceType.MATERIAL]],
        "minimum_should_match": 1,
        "should": [
            qmatch(**{"path": noderef_id}),
            qmatch(**{"nodeRef.id": noderef_id}),
        ],
        "must_not": Q("wildcard", **{missing_attribute: {"value": "*"}}),
    }

    return (
        Search()
        .base_filters()
        .query(qbool(**query))
        .source(includes=[source.path for source in LearningMaterial.source_fields])[
            :max_hits
        ]
    )


all_source_fields: list = [
    ElasticResourceAttribute.NODEREF_ID,
    ElasticResourceAttribute.TYPE,
    ElasticResourceAttribute.NAME,
    CollectionAttribute.TITLE,
    ElasticResourceAttribute.KEYWORDS,
    CollectionAttribute.DESCRIPTION,
    CollectionAttribute.PATH,
    CollectionAttribute.PARENT_ID,
]


def missing_materials_search(
    noderef_id: UUID,
    missing_attr_filter: Optional[MissingAttributeFilter],
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
):
    print(missing_attr_filter)
    print(missing_attr_filter.attr)
    # # TODO: Why is there collections. in the match?
    # query = {
    #     "filter": [*type_filter[ResourceType.MATERIAL]],
    #     "minimum_should_match": 1,
    #     "should": [
    #         qmatch(**{"collections.path": noderef_id}),
    #         qmatch(**{"collections.nodeRef.id": noderef_id}),
    #     ],
    #     "must_not": Q("wildcard", **{missing_attr_filter.attr: {"value": "*"}}),
    # }
    #
    # return (
    #     Search()
    #     .base_filters()
    #     .query(qbool(**query))
    #     .source(includes=[source.path for source in all_source_fields])[:max_hits]
    # )
    query_dict = get_many_base_query(
        resource_type=ResourceType.MATERIAL,
        ancestor_id=noderef_id,
    )
    if missing_attr_filter:
        query_dict = missing_attr_filter.__call__(query_dict=query_dict)
    s = Search().query(qbool(**query_dict))
    all_source_fields_old = [
        (field.path if isinstance(field, ElasticField) else field)
        for field in LearningMaterial.source_fields
    ]
    search = s.source(all_source_fields_old)[:max_hits]
    return search


async def get_many(
    ancestor_id: Optional[UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
    source_fields: Optional[set[LearningMaterialAttribute]] = None,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[LearningMaterial]:
    search = missing_materials_search(
        ancestor_id, missing_attr_filter, max_hits=max_hits
    )

    print(search.to_dict())
    response = search.execute()
    print(response)
    search = missing_attributes_search(
        ancestor_id, missing_attr_filter.attr.value, max_hits
    )
    response = search.execute()
    if response.success():
        return [LearningMaterial.parse_elastic_hit(hit) for hit in response]


async def get_child_materials_with_missing_attributes(
    noderef_id: UUID,
    missing_attr_filter: MissingAttributeFilter,
    source_fields: Optional[set[LearningMaterialAttribute]],
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[LearningMaterial]:
    return await get_many(
        ancestor_id=noderef_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=source_fields,
        max_hits=max_hits,
    )


def filter_response_fields(
    items: list[BaseModel], response_fields: set[ElasticField] = None
) -> list[BaseModel]:
    if response_fields:
        return [
            i.copy(include={f.name.lower() for f in response_fields}) for i in items
        ]
    return items