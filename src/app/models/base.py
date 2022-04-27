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
