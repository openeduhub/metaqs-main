import uuid
from typing import ClassVar, Optional, Type, TypeVar

from elasticsearch_dsl import Q
from fastapi.params import Path, Query
from glom import Coalesce, Iter, glom
from pydantic import BaseModel, Extra
from pydantic.validators import str_validator

from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import LearningMaterialAttribute, ResponseModel
from app.elastic.dsl import ElasticField, qbool, qmatch
from app.elastic.elastic import (
    ResourceType,
    query_missing_material_license,
    type_filter,
)
from app.elastic.search import Search
from app.models import _ELASTIC_RESOURCE, ElasticResourceAttribute

_LEARNING_MATERIAL = TypeVar("_LEARNING_MATERIAL")


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
    noderef_id: uuid.UUID
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
            LearningMaterialAttribute.TITLE,
            LearningMaterialAttribute.LEARNINGRESOURCE_TYPE,
            LearningMaterialAttribute.SUBJECTS,  # TODO: Refactor to TaxonId
            LearningMaterialAttribute.WWW_URL,
            LearningMaterialAttribute.LICENSES,
            LearningMaterialAttribute.PUBLISHER,
            LearningMaterialAttribute.DESCRIPTION,
            LearningMaterialAttribute.EDUENDUSERROLE_DE,
            LearningMaterialAttribute.EDU_CONTEXT,
        ]
    ],
)


class MissingAttributeFilter(BaseModel):
    attr: MissingMaterialField


def materials_filter_params(
    *, missing_attr: MissingMaterialField = Path(...)
) -> MissingAttributeFilter:
    return MissingAttributeFilter(attr=missing_attr)


def missing_attributes_search(
    node_id: uuid.UUID, missing_attribute: str, max_hits: int
) -> Search:
    query = {
        "minimum_should_match": 1,
        "should": [
            qmatch(**{"collections.path": node_id}),
            qmatch(**{"collections.nodeRef.id": node_id}),
        ],
        "filter": type_filter[
            ResourceType.MATERIAL
        ].copy(),  # copy otherwise appending the query causes mutation
    }
    query["filter"].append(
        Q("bool", **{"must_not": [{"term": {"aspects": "ccm:io_childobject"}}]})
    )
    query["filter"].append(Q({"term": {"content.mimetype.keyword": "text/plain"}}))
    if missing_attribute == LearningMaterialAttribute.LICENSES.path:
        query["filter"].append(query_missing_material_license().to_dict())
    else:
        query.update(
            {
                "must_not": Q("wildcard", **{missing_attribute: {"value": "*"}}),
            }
        )

    return (
        Search()
        .base_filters()
        .query(qbool(**query))
        .source(includes=[source.path for source in LearningMaterial.source_fields])[
            :max_hits
        ]
    )


async def search_materials_with_missing_attributes(
    node_id: Optional[uuid.UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
) -> list[LearningMaterial]:
    search = missing_attributes_search(
        node_id, missing_attr_filter.attr.value, ELASTIC_TOTAL_SIZE
    )
    response = search.execute()
    if response.success():
        return [LearningMaterial.parse_elastic_hit(hit) for hit in response]


def filter_response_fields(
    items: list[BaseModel], response_fields: set[ElasticField] = None
) -> list[BaseModel]:
    if response_fields:
        return [
            i.copy(include={f.name.lower() for f in response_fields}) for i in items
        ]
    return items


async def get_materials_with_missing_attributes(
    missing_attr_filter, node_id, response_fields
):
    if response_fields:
        response_fields.add(LearningMaterialAttribute.NODEREF_ID)
    materials = await search_materials_with_missing_attributes(
        node_id=node_id,
        missing_attr_filter=missing_attr_filter,
    )
    return filter_response_fields(materials, response_fields=response_fields)
