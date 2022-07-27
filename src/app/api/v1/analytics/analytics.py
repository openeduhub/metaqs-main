from collections import defaultdict
from datetime import datetime
from typing import List
from uuid import UUID

from asyncpg import Pool
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from src.app.api.util import portal_id_param
from src.app.crud.util import StatsNotFoundException, build_portal_tree
from src.app.models.collection import Collection, PortalTreeNode
from src.app.models.oeh_validation import MaterialFieldValidation, OehValidationError
from src.app.models.stats import (
    CollectionValidationStats,
    MaterialValidationStats,
    StatsResponse,
    StatType,
    ValidationStatsResponse,
)
from src.app.pg.queries import stats_latest
from src.app.pg.util import get_postgres_async

router = APIRouter()


@router.get(
    "/{noderef_id}",
    response_model=StatsResponse,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats(
    *,
    noderef_id: UUID = Depends(portal_id_param),
    pool: Pool = Depends(get_postgres_async),
):
    async with pool.acquire() as conn:
        search_stats = await stats_latest(
            conn=conn, stat_type=StatType.SEARCH, noderef_id=noderef_id
        )

        if not search_stats:
            raise StatsNotFoundException

        material_types_stats = await stats_latest(
            conn=conn, stat_type=StatType.MATERIAL_TYPES, noderef_id=noderef_id
        )

        if not material_types_stats:
            raise StatsNotFoundException

    stats = defaultdict(dict)

    for stat in search_stats:
        stats[str(stat["collection_id"])]["search"] = stat["stats"]

    for stat in material_types_stats:
        stats[str(stat["collection_id"])]["material_types"] = stat["counts"]

    return StatsResponse(
        derived_at=datetime.fromtimestamp(0),
        stats=stats,
    )


@router.get(
    "/{noderef_id}/validation",
    response_model=List[ValidationStatsResponse[MaterialValidationStats]],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats_validation(
    *,
    noderef_id: UUID = Depends(portal_id_param),
    pool: Pool = Depends(get_postgres_async),
):
    async with pool.acquire() as conn:
        stats = await stats_latest(
            conn=conn, stat_type=StatType.VALIDATION_MATERIALS, noderef_id=noderef_id
        )

    if not stats:
        raise StatsNotFoundException

    response = [
        ValidationStatsResponse[MaterialValidationStats](
            noderef_id=stat["collection_id"],
            validation_stats=MaterialValidationStats(
                **{
                    field.lower(): MaterialFieldValidation(missing=material_ids)
                    for field, material_ids in stat["missing_fields"].items()
                },
            ),
        )
        for stat in stats
    ]

    return response


@router.get(
    "/{noderef_id}/validation/collections",
    response_model=List[ValidationStatsResponse[CollectionValidationStats]],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats_validation_collection(
    *,
    noderef_id: UUID = Depends(portal_id_param),
    pool: Pool = Depends(get_postgres_async),
):
    async with pool.acquire() as conn:
        stats = await stats_latest(
            conn=conn, stat_type=StatType.VALIDATION_COLLECTIONS, noderef_id=noderef_id
        )

    if not stats:
        raise StatsNotFoundException

    response = [
        ValidationStatsResponse[CollectionValidationStats](
            noderef_id=stat["collection_id"],
            validation_stats=CollectionValidationStats(
                **{
                    k.lower(): [OehValidationError.MISSING]
                    for k in stat["missing_fields"]
                }
            ),
        )
        for stat in stats
    ]

    return response


@router.get(
    "/{noderef_id}/portal-tree",
    response_model=List[PortalTreeNode],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats_portal_tree(
    *,
    noderef_id: UUID = Depends(portal_id_param),
    pool: Pool = Depends(get_postgres_async),
):
    async with pool.acquire() as conn:
        stats = await stats_latest(
            conn=conn, stat_type=StatType.PORTAL_TREE, noderef_id=noderef_id
        )

    if not stats:
        raise StatsNotFoundException

    return await build_portal_tree(
        collections=[Collection(**c) for c in stats], root_noderef_id=noderef_id
    )
