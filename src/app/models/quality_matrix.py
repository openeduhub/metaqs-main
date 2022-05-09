import asyncio

from pydantic import Field, create_model

from app.core.config import RUNNING_WITH_ELASTICSEARCH
from app.core.constants import PERCENTAGE_DESCRIPTOR
from app.crud.replication_sources import all_sources
from app.elastic.utils import close_elastic_connection, connect_to_elastic
from app.models.base import BaseModel


def sources_transformed_to_field_list(sources: dict) -> dict[str, Field]:
    return {
        k: Field(default=0, description=PERCENTAGE_DESCRIPTOR) for k in sources.keys()
    }


def all_sources_for_open_api() -> dict[str:float]:
    if RUNNING_WITH_ELASTICSEARCH:
        asyncio.run(connect_to_elastic())
        sources = sources_transformed_to_field_list(all_sources())
        asyncio.run(close_elastic_connection())
    else:
        sources = {}
    return sources


ColumnOutputModel = create_model(
    "ColumnOutputModel",
    metadatum=Field(default="", description="Name of the evaluated metadatum."),
    **all_sources_for_open_api(),
    __base__=BaseModel,
)


class MissingCollectionProperties(BaseModel):
    total: int = Field(default=0, gt=0, description="Number of entries")
    short_description: float = Field(
        default=0.0,
        gt=0.0,
        le=1.0,
        description="Ratio of entries without short description",
    )
    short_title: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without short title"
    )
    missing_edu_context: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_description: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without description"
    )
    few_keywords: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries with few keywords"
    )
    missing_keywords: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without title"
    )


class MissingMaterialProperties(BaseModel):
    total: int = Field(default=0, gt=0, description="Number of entries")
    missing_edu_context: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_object_type: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without object type"
    )
    missing_description: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without description"
    )
    missing_license: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries with missing license"
    )
    missing_keywords: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without title"
    )
    missing_ads_qualifier: float = Field(
        default=0.0,
        gt=0.0,
        le=1.0,
        description="Ratio of entries missing advertisement qualifier",
    )
    missing_subjects: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries missing subjects"
    )
    missing_material_type: float = Field(
        default=0.0,
        gt=0.0,
        le=1.0,
        description="Ratio of entries missing material type",
    )


class ScoreOutput(BaseModel):
    score: int = Field(default=0, gt=0, le=100, description="Overall score")
    collections: MissingCollectionProperties = Field(
        description="Score for specific collection properties"
    )
    materials: MissingMaterialProperties = Field(
        description="Score for specific material properties"
    )
