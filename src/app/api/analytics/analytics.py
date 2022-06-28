from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Extra
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND


class StatType(str, Enum):
    PORTAL_TREE = "portal-tree"
    SEARCH = "search"
    MATERIAL_TYPES = "material-types"
    VALIDATION_COLLECTIONS = "validation-collections"
    VALIDATION_MATERIALS = "validation-materials"


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
