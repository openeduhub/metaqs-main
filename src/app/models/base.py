from pydantic import BaseModel as _BaseModel
from pydantic import Extra

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
