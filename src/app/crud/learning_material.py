from random import randint
from typing import List, Optional, Set
from uuid import UUID

from elasticsearch_dsl.function import RandomScore
from elasticsearch_dsl.query import FunctionScore
from elasticsearch_dsl.response import Response
from glom import Iter, glom
from pydantic import BaseModel

# from app.core.util import slugify
from app.core.config import ELASTIC_MAX_SIZE
from app.elastic import Field, Search, qbool, qwildcard
from app.models.learning_material import LearningMaterial, LearningMaterialAttribute

from .elastic import (
    ResourceType,
    agg_material_types,
    get_many_base_query,
    query_materials,
    query_missing_material_license,
)

MissingMaterialField = Field(
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


class MissingAttributeFilter(BaseModel):
    attr: MissingMaterialField

    def __call__(self, query_dict: dict):
        if self.attr == LearningMaterialAttribute.LICENSES:
            query_dict["filter"].append(query_missing_material_license())
        else:
            query_dict["must_not"] = qwildcard(qfield=self.attr, value="*")

        return query_dict


async def get_many(
    ancestor_id: Optional[UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
    source_fields: Optional[Set[LearningMaterialAttribute]] = None,
    max_hits: Optional[int] = ELASTIC_MAX_SIZE,
) -> List[LearningMaterial]:
    query_dict = get_many_base_query(
        resource_type=ResourceType.MATERIAL,
        ancestor_id=ancestor_id,
    )
    if missing_attr_filter:
        query_dict = missing_attr_filter.__call__(query_dict=query_dict)
    s = Search().query(qbool(**query_dict))

    response = s.source(
        source_fields if source_fields else LearningMaterial.source_fields
    )[:max_hits].execute()

    if response.success():
        return [LearningMaterial.parse_elastic_hit(hit) for hit in response]


async def get_random(
    ancestor_id: Optional[UUID] = None,
    source_fields: Optional[Set[LearningMaterialAttribute]] = None,
) -> LearningMaterial:
    s = Search().query(
        FunctionScore(
            query=query_materials(ancestor_id=ancestor_id),
            functions=RandomScore(seed=randint(1, 2**32 - 1), field="_seq_no"),
            boost_mode="sum",
        )
    )

    response = s.source(
        source_fields if source_fields else LearningMaterial.source_fields
    )[:1].execute()

    if response.success():
        return LearningMaterial.parse_elastic_hit(response.hits[0])


async def material_count(ancestor_id: UUID) -> int:
    s = Search().query(query_materials(ancestor_id=ancestor_id))

    response: Response = s[:0].execute()

    if response.success():
        return response.hits.total.value


async def material_types() -> List[str]:
    s = Search().query(query_materials())
    s.aggs.bucket("material_types", agg_material_types())

    response: Response = s[:0].execute()

    if response.success():
        # TODO: refactor algorithm
        return glom(
            response.aggregations.material_types.buckets,
            # (Iter("key").map(lambda k: {slugify(k): k}).all(), merge,),
            Iter("key").all(),
        )


# async def material_types_lut() -> dict:
#     mt = await get_material_types()
#     return {v: k for k, v in mt.items()}
