import uuid
from datetime import datetime
from enum import Enum
from typing import ClassVar, Generic, Optional, TypeVar

from pydantic import BaseModel, Extra, Field, validator
from pydantic.generics import GenericModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.core.models import ResponseModel


class StatType(str, Enum):
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


CountStatistics = dict[str, int]


class StatsResponse(ResponseModel):
    """
    In principle this class is a four-dimensional array with the dimension:
     - collection (node_id, the most outer dictionary keys)
     - Sammlung|Suche (mid level dictionary keys)
     - content type (Picture, Video, ..., lowes level keys, within CountStatistics)
     - total_stats vs oer_stats
    """

    derived_at: datetime
    total_stats: dict[
        str, dict[str, CountStatistics]
    ]  # node_id: search/material_types: UUID of the material
    oer_stats: dict[
        str, dict[str, CountStatistics]
    ]  # node_id: search/material_types: UUID of the material


ValidationStatsT = TypeVar("ValidationStatsT")


class ValidationStatsResponse(GenericModel, Generic[ValidationStatsT]):
    noderef_id: uuid.UUID
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
    missing: Optional[list[uuid.UUID]]
    too_short: Optional[list[uuid.UUID]]
    too_few: Optional[list[uuid.UUID]]
    lacks_clarity: Optional[list[uuid.UUID]]
    invalid_spelling: Optional[list[uuid.UUID]]

    # validators
    _none_to_empty_list = validator("*", pre=True, allow_reuse=True)(none_to_empty_list)


class MaterialValidationStats(ElasticValidationStats[MaterialFieldValidation]):
    subjects: Optional[MaterialFieldValidation]
    license: Optional[MaterialFieldValidation]
    url: Optional[MaterialFieldValidation]
    publisher: Optional[MaterialFieldValidation]
    intended_end_user_role: Optional[MaterialFieldValidation]
    material_type: Optional[MaterialFieldValidation]
