from datetime import datetime
from enum import Enum
from typing import ClassVar, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Extra, Field
from pydantic.generics import GenericModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND


class StatType(str, Enum):
    # PORTAL_TREE = "portal-tree"  # Currently unused
    SEARCH = "search"
    MATERIAL_TYPES = "material-types"
    VALIDATION_COLLECTIONS = "validation-collections"
    # VALIDATION_MATERIALS = "validation-materials"  # Currently unused


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


async def stats_latest(conn, stat_type: StatType, noderef_id: UUID) -> list[dict]:
    results = []
    print(conn, stat_type, noderef_id)
    results = [dict(record) for record in results]

    return results


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
