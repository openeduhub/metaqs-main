from datetime import datetime
from enum import Enum
from typing import Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import Field
from pydantic.generics import GenericModel

from .base import ResponseModel
from .oeh_validation import MaterialFieldValidation, OehValidationError


class StatType(str, Enum):
    PORTAL_TREE = "portal-tree"
    SEARCH = "search"
    MATERIAL_TYPES = "material-types"
    VALIDATION_COLLECTIONS = "validation-collections"
    VALIDATION_MATERIALS = "validation-materials"


ElasticFieldValidationT = TypeVar("ElasticFieldValidationT")
ValidationStatsT = TypeVar("ValidationStatsT")


class StatsResponse(ResponseModel):
    derived_at: datetime
    stats: Dict[str, Dict[str, Dict[str, int]]]


class ElasticValidationStats(GenericModel, Generic[ElasticFieldValidationT]):
    title: Optional[ElasticFieldValidationT]
    keywords: Optional[ElasticFieldValidationT]
    description: Optional[ElasticFieldValidationT]
    edu_context: Optional[ElasticFieldValidationT]


class CollectionValidationStats(ElasticValidationStats[List[OehValidationError]]):
    pass


class MaterialValidationStats(ElasticValidationStats[MaterialFieldValidation]):
    subjects: Optional[MaterialFieldValidation]
    license: Optional[MaterialFieldValidation]
    ads_qualifier: Optional[MaterialFieldValidation]
    material_type: Optional[MaterialFieldValidation]
    object_type: Optional[MaterialFieldValidation]


class ValidationStatsResponse(GenericModel, Generic[ValidationStatsT]):
    noderef_id: UUID
    derived_at: datetime = Field(default_factory=datetime.now)
    validation_stats: ValidationStatsT
