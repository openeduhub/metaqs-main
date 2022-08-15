import uuid
from datetime import datetime
from enum import Enum
from typing import ClassVar, Generic, Optional, TypeVar

from pydantic import BaseModel, Extra, Field
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
    oer_ratio: int = Field(default=0)


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


class MaterialValidationStats(BaseModel):
    """
    The UUIDs within the optional lists identify materials.
    """

    subjects: Optional[list[uuid.UUID]]
    license: Optional[list[uuid.UUID]]
    url: Optional[list[uuid.UUID]]
    publisher: Optional[list[uuid.UUID]]
    intended_end_user_role: Optional[list[uuid.UUID]]
    material_type: Optional[list[uuid.UUID]]
    title: Optional[list[uuid.UUID]]
    keywords: Optional[list[uuid.UUID]]
    description: Optional[list[uuid.UUID]]
    edu_context: Optional[list[uuid.UUID]]


class MaterialValidationResponse(BaseModel):
    collection_id: uuid.UUID
    derived_at: datetime = Field(default_factory=datetime.now)
    stats: MaterialValidationStats


class PendingMaterials(BaseModel):
    # title: 'Materialien ohne Titel',
    # learning_resource_type: 'Materialien ohne Kategorie',
    # taxon_id: 'Materialien ohne Fachgebiet',
    # license: 'Materialien ohne Lizenz',
    # publisher: 'Materialien ohne Herkunft',
    # description: 'Materialien ohne Beschreibungstext',
    # intended_end_user_role: 'Materialien ohne Zielgruppe',
    # edu_context: 'Materialien ohne Bildungsstufe',       

    collection_id: uuid.UUID
    title: list[uuid.UUID]
    edu_context: list[uuid.UUID]
    url: list[uuid.UUID]
    description: list[uuid.UUID]
    license: list[uuid.UUID]
    learning_resource_type: list[uuid.UUID]
    taxon_id: list[uuid.UUID]
    publisher: list[uuid.UUID]
    intended_end_user_role: list[uuid.UUID]


class PendingMaterialsResponse(BaseModel):
    collection_id: uuid.UUID
    missing_materials: list[PendingMaterials]
