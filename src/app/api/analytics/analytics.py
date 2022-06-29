from datetime import datetime
from enum import Enum
from typing import ClassVar, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Extra, Field, validator
from pydantic.generics import GenericModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND


class StatType(str, Enum):
    # PORTAL_TREE = "portal-tree"  # Currently unused
    SEARCH = "search"
    MATERIAL_TYPES = "material-types"
    VALIDATION_COLLECTIONS = "validation-collections"
    VALIDATION_MATERIALS = "validation-materials"  # Currently unused


class StatsNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_404_NOT_FOUND,
            detail="Stats not found",
        )


class ElasticConfig:
    allow_population_by_field_name = True
    extra = Extra.allow


class ElasticModel(BaseModel):
    class Config(ElasticConfig):
        pass


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass


class StatsResponse(ResponseModel):
    derived_at: datetime
    stats: dict[str, dict[str, dict[str, int]]]


ValidationStatsT = TypeVar("ValidationStatsT")


class ValidationStatsResponse(GenericModel, Generic[ValidationStatsT]):
    noderef_id: UUID
    derived_at: datetime = Field(default_factory=datetime.now)
    validation_stats: ValidationStatsT


ElasticFieldValidationT = TypeVar("ElasticFieldValidationT")


class ElasticValidationStats(GenericModel, Generic[ElasticFieldValidationT]):
    title: Optional[ElasticFieldValidationT]
    keywords: Optional[ElasticFieldValidationT]
    description: Optional[ElasticFieldValidationT]
    edu_context: Optional[ElasticFieldValidationT]


class OehValidationError(str, Enum):
    MISSING = "missing"
    TOO_SHORT = "too_short"
    TOO_FEW = "too_few"
    LACKS_CLARITY = "lacks_clarity"
    INVALID_SPELLING = "invalid_spelling"

    _lut: ClassVar[dict]


class CollectionValidationStats(ElasticValidationStats[list[OehValidationError]]):
    pass


def none_to_empty_list(v: list) -> Optional[list]:
    if v is None:
        return []
    return v


class MaterialFieldValidation(BaseModel):
    missing: Optional[list[UUID]]
    too_short: Optional[list[UUID]]
    too_few: Optional[list[UUID]]
    lacks_clarity: Optional[list[UUID]]
    invalid_spelling: Optional[list[UUID]]

    # validators
    _none_to_empty_list = validator("*", pre=True, allow_reuse=True)(none_to_empty_list)


class MaterialValidationStats(ElasticValidationStats[MaterialFieldValidation]):
    subjects: Optional[MaterialFieldValidation]
    license: Optional[MaterialFieldValidation]
    ads_qualifier: Optional[MaterialFieldValidation]
    material_type: Optional[MaterialFieldValidation]
    object_type: Optional[MaterialFieldValidation]
