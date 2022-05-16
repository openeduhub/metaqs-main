from typing import List, Optional
from uuid import UUID

from databases import Database
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.api.quality_matrix.models import ColumnOutputModel
from app.api.quality_matrix.quality_matrix import quality_matrix
from app.api.quality_matrix.timeline import timestamps
from app.api.score.models import ScoreOutput
from app.api.score.score import (
    calc_scores,
    calc_weighted_score,
    collection_id_param,
    query_score,
)
from app.elastic.elastic import (
    ResourceType,
    aggs_collection_validation,
    aggs_material_validation,
    field_names_used_for_score_calculation,
)


def get_database(request: Request) -> Database:
    return request.app.state._db


router = APIRouter()

QUALITY_MATRIX_DESCRIPTION = """Calculation of the quality matrix.
    For each replication source and each property, e.g., `cm:creator`, the quality matrix returns the ratio of
    elements which miss this entry compared to the total number of entries.
    A missing entry may be `cm:creator = null`."""
TAG_STATISTICS = "Statistics"


@router.get(
    "/quality_matrix",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION,
)
async def get_quality_matrix(database: Database = Depends(get_database)):
    return await quality_matrix(database)


@router.get(
    "/quality_matrix/{timestamp}",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION
    + """A timestamp of the format XYZ yields the quality matrix at the respective date.""",
)
async def get_past_quality_matrix(timestamp: Optional[int] = None):
    print(timestamp)
    return await quality_matrix()


@router.get(
    "/quality_matrix_timestamps",
    status_code=HTTP_200_OK,
    response_model=List[int],
    responses={
        HTTP_404_NOT_FOUND: {
            "description": "Timestamps of old quality matrix results not determinable"
        }
    },
    tags=[TAG_STATISTICS],
    description="""Return timestamps of the format XYZ of past calculations of the quality matrix.""",
)
async def get_timestamps(database: Database = Depends(get_database)):
    return await timestamps(database)


@router.get(
    "/collections/{collection_id}/stats/score",
    response_model=ScoreOutput,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[TAG_STATISTICS],
    description=f"""Returns the average ratio of non-empty properties for the chosen collection.
    For certain properties, e.g. `properties.cclom:title`, the ratio of
    elements which miss this entry compared to the total number of entries is calculated.
    A missing entry may be `properties.cclom:title = null`. Not all properties are considered here.
    The overall score is the average of all these ratios.
    The queried properties are:
    `{field_names_used_for_score_calculation(aggs_collection_validation)
      + field_names_used_for_score_calculation(aggs_material_validation)}`.
    """,
)
async def score(*, collection_id: UUID = Depends(collection_id_param)):
    collection_stats = await query_score(
        noderef_id=collection_id, resource_type=ResourceType.COLLECTION
    )

    collection_scores = calc_scores(stats=collection_stats)

    material_stats = await query_score(
        noderef_id=collection_id, resource_type=ResourceType.MATERIAL
    )

    material_scores = calc_scores(stats=material_stats)

    score_ = calc_weighted_score(
        collection_scores=collection_scores,
        material_scores=material_scores,
    )

    return {
        "score": score_,
        "collections": {"total": collection_stats["total"], **collection_scores},
        "materials": {"total": material_stats["total"], **material_scores},
    }


class Ping(BaseModel):
    status: str = Field(
        default="not ok",
        description="Ping output. Should be 'ok' in happy case.",
    )


@router.get(
    "/_ping",
    description="Ping function for automatic health check.",
    response_model=Ping,
    tags=["Healthcheck"],
)
async def ping_api():
    return {"status": "ok"}
