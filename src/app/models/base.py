from typing import Optional

from pydantic import BaseModel as _BaseModel
from pydantic import Extra, Field

from app.core.constants import PERCENTAGE_DESCRIPTOR

AUTO_UNIQUE_STRING = "AUTO_UNIQUE_STRING"


class BaseModel(_BaseModel):
    pass


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


class RequestConfig:
    allow_population_by_field_name = False
    extra = Extra.forbid


class RequestModel(BaseModel):
    class Config(RequestConfig):
        pass


class Property(BaseModel):
    empty: int = Field(default=0)
    not_empty: int = Field(default=0)
    total_count: int = Field(default=0)


class ColumnOutput(BaseModel):
    metadatum: str = Field(default="", description="Name of the evaluated metadatum.")
    bpb_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    br_rss_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    geogebra_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    oai_sodis_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    rpi_virtuell_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    serlo_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    tutory_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    youtube_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    zum_klexikon_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    zum_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)


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
