import uuid
from typing import Optional

from elasticsearch_dsl import Q
from fastapi.params import Path, Query
from glom import Coalesce, Iter
from pydantic import BaseModel, Extra
from pydantic.validators import str_validator

from app.api.collections.utils import map_elastic_response_to_model
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import ElasticResourceAttribute, ResponseModel
from app.elastic.dsl import ElasticField, qbool, qmatch
from app.elastic.elastic import (
    ResourceType,
    query_missing_material_license,
    type_filter,
)
from app.elastic.search import Search


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


missing_materials_spec = {
    "title": Coalesce(ElasticResourceAttribute.TITLE.path, default=None),
    "keywords": (
        Coalesce(ElasticResourceAttribute.KEYWORDS.path, default=[]),
        Iter().all(),
    ),
    "edu_context": (
        Coalesce(ElasticResourceAttribute.EDU_CONTEXT.path, default=[]),
        Iter().all(),
    ),
    "subjects": (
        Coalesce(ElasticResourceAttribute.SUBJECTS.path, default=[]),
        Iter().all(),
    ),
    "www_url": Coalesce(ElasticResourceAttribute.WWW_URL.path, default=None),
    "description": (
        Coalesce(ElasticResourceAttribute.DESCRIPTION.path, default=[]),
        (Iter().all(), "\n".join),
    ),
    "licenses": (
        Coalesce(ElasticResourceAttribute.LICENSES.path, default=[]),
        (Iter().all(), "\n".join),
    ),
    "node_id": ElasticResourceAttribute.NODE_ID.path,
    "type": Coalesce(ElasticResourceAttribute.TYPE.path, default=None),
    "name": Coalesce(ElasticResourceAttribute.NAME.path, default=None),
}


class LearningMaterial(ResponseModel):
    node_id: uuid.UUID
    type: Optional[EmptyStrToNone] = None
    name: Optional[EmptyStrToNone] = None
    title: Optional[EmptyStrToNone] = None
    keywords: Optional[list[str]] = None
    edu_context: Optional[list[str]] = None
    subjects: Optional[list[str]] = None
    www_url: Optional[str] = None
    description: Optional[EmptyStrToNone] = None
    licenses: Optional[EmptyStrToNone] = None

    class Config(ElasticConfig):
        pass


def material_response_fields(
    *, response_fields: set[ElasticResourceAttribute] = Query(None)
) -> set[ElasticResourceAttribute]:
    return response_fields


missing_attributes_source_fields = {
    ElasticResourceAttribute.TITLE,
    ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
    ElasticResourceAttribute.SUBJECTS,
    ElasticResourceAttribute.WWW_URL,
    ElasticResourceAttribute.LICENSES,
    ElasticResourceAttribute.PUBLISHER,
    ElasticResourceAttribute.DESCRIPTION,
    ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
    ElasticResourceAttribute.EDU_CONTEXT,
    ElasticResourceAttribute.COVER,
    ElasticResourceAttribute.NODE_ID,
    ElasticResourceAttribute.TYPE,
    ElasticResourceAttribute.NAME,
    ElasticResourceAttribute.KEYWORDS,
}

MissingMaterialField = ElasticField(
    "MissingMaterialField",
    [(f.name, (f.value, f.field_type)) for f in missing_attributes_source_fields],
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
        "filter": [
            *type_filter[
                ResourceType.MATERIAL
            ].copy(),  # copy otherwise appending the query causes mutation
            Q("bool", **{"must_not": [{"term": {"aspects": "ccm:io_childobject"}}]}),
            Q({"term": {"content.mimetype.keyword": "text/plain"}}),
        ],
    }
    if missing_attribute == ElasticResourceAttribute.LICENSES.path:
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
        .source(includes=[source.path for source in missing_attributes_source_fields])[
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
        return map_elastic_response_to_model(
            response, missing_materials_spec, LearningMaterial
        )


# TODO is this really being used?
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
        response_fields.add(ElasticResourceAttribute.NODE_ID)
    materials = await search_materials_with_missing_attributes(
        node_id=node_id,
        missing_attr_filter=missing_attr_filter,
    )
    return filter_response_fields(materials, response_fields=response_fields)
