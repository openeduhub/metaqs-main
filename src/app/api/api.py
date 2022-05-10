from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from starlette_context import context

from app.api.score.score import calc_scores, calc_weighted_score
from app.api.util import collection_id_param
from app.crud import stats as crud_stats
from app.crud.elastic import (
    ResourceType,
    aggs_collection_validation,
    aggs_material_validation,
    field_names_used_for_score_calculation,
)
from app.crud.quality_matrix import quality_matrix
from app.models.base import ColumnOutput, ScoreOutput

router = APIRouter()


@router.get(
    "/quality_matrix",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutput],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=["Statistics"],
    description="""Calculation of the quality matrix.
    For each replication source and each property, e.g., `cm:creator`, the quality matrix returns the ratio of
    elements which miss this entry compared to the total number of entries.
    A missing entry may be `cm:creator = null`.""",
)
async def get_quality_matrix():
    return await quality_matrix()


@router.get(
    "/collections/{collection_id}/stats/score",
    response_model=ScoreOutput,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Statistics"],
    description=f"""Returns the average ratio of non-empty properties for the chosen collection.
    For certain properties, e.g. `properties.cclom:title`, the ratio of
    elements which miss this entry compared to the total number of entries is calculated.
    A missing entry may be `properties.cclom:title = null`. Not all properties are considered here.
    The overall score is the average of all these ratios.
    The queried properties are:
    `{field_names_used_for_score_calculation(aggs_collection_validation)
      + field_names_used_for_score_calculation(aggs_material_validation)}`
    """,
)
async def score(
    *,
    collection_id: UUID = Depends(collection_id_param),
    response: Response,
):
    collection_stats = await crud_stats.query_score(
        noderef_id=collection_id, resource_type=ResourceType.COLLECTION
    )

    collection_scores = calc_scores(stats=collection_stats)

    material_stats = await crud_stats.query_score(
        noderef_id=collection_id, resource_type=ResourceType.MATERIAL
    )

    material_scores = calc_scores(stats=material_stats)

    score_ = calc_weighted_score(
        collection_scores=collection_scores,
        material_scores=material_scores,
    )

    response.headers["X-Query-Count"] = str(len(context.get("elastic_queries", [])))
    return {
        "score": score_,
        "collections": {"total": collection_stats["total"], **collection_scores},
        "materials": {"total": material_stats["total"], **material_scores},
    }
