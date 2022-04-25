from typing import List

from pydantic import BaseModel as _BaseModel
from pydantic import Extra, Field

from app.core.constants import REPLICATION_SOURCE

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
    column_name: str = Field(default="", description="column name")
    # replication_source: Property = Field(default="", alias=REPLICATION_SOURCE)
    # creator: Property = Field(default=None, alias="cm.creator")
