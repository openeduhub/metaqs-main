from pydantic import BaseModel, Extra


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass
