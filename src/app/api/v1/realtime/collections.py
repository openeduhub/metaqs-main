from typing import List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from starlette_context import context

import app.crud.collection as crud_collection
import app.crud.stats as crud_stats
from app.api.util import (
    collection_response_fields,
    collections_filter_params,
    filter_response_fields,
    portal_id_param,
    portal_id_with_root_param,
)
from app.core.config import ENABLE_COLLECTIONS_API
from app.crud import MissingCollectionAttributeFilter
from app.crud.elastic import ResourceType
from app.crud.quality_matrix import all_sources, quality_matrix
from app.crud.util import build_portal_tree
from app.models.base import ColumnOutput, ScoreOutput
from app.models.collection import (
    Collection,
    CollectionAttribute,
    CollectionMaterialsCount,
    PortalTreeNode,
)
from app.score import ScoreModulator, ScoreWeights, calc_scores, calc_weighted_score

router = APIRouter()


@router.get(
    "/quality_matrix",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutput],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=["Statistics"],
)
async def get_quality_matrix():
    return await quality_matrix()


if ENABLE_COLLECTIONS_API:

    @router.get(
        "/sources",
        status_code=HTTP_200_OK,
        responses={HTTP_404_NOT_FOUND: {"description": "Sources not determinable"}},
        tags=["Statistics"],
    )
    async def get_replication_sources():
        return all_sources()

    @router.get(
        "/collections",
        tags=["Collections"],
    )
    async def get_portals():
        return await crud_collection.get_portals()

    @router.get(
        "/collections/{noderef_id}/tree",
        response_model=List[PortalTreeNode],
        status_code=HTTP_200_OK,
        responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
        tags=["Collections"],
    )
    async def get_portal_tree(
        *,
        noderef_id: UUID = Depends(portal_id_with_root_param),
        response: Response,
    ):
        collections = await crud_collection.get_many_sorted(root_noderef_id=noderef_id)
        tree = await build_portal_tree(
            collections=collections, root_noderef_id=noderef_id
        )
        response.headers["X-Total-Count"] = str(len(collections))
        response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
        return tree

    @router.get(
        "/collections/{noderef_id}/pending-subcollections/{missing_attr}",
        response_model=List[Collection],
        response_model_exclude_unset=True,
        status_code=HTTP_200_OK,
        responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
        tags=["Collections"],
    )
    async def filter_collections_with_missing_attributes(
        *,
        noderef_id: UUID = Depends(portal_id_with_root_param),
        missing_attr_filter: MissingCollectionAttributeFilter = Depends(
            collections_filter_params
        ),
        response_fields: Optional[Set[CollectionAttribute]] = Depends(
            collection_response_fields
        ),
        response: Response,
    ):
        if response_fields:
            response_fields.add(CollectionAttribute.NODEREF_ID)

        collections = (
            await crud_collection.get_child_collections_with_missing_attributes(
                noderef_id=noderef_id,
                missing_attr_filter=missing_attr_filter,
                source_fields=response_fields,
            )
        )

        response.headers["X-Total-Count"] = str(len(collections))
        response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
        return filter_response_fields(collections, response_fields=response_fields)

    @router.get(
        "/stats/search/material-type",
        response_model=dict,
        status_code=HTTP_200_OK,
        tags=["Statistics"],
    )
    async def search_hits_by_material_type(
        *, query_str: str = Query(..., min_length=3, max_length=50), response: Response
    ):
        search_stats = crud_stats.search_hits_by_material_type(query_str)

        response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
        return search_stats

    @router.get(
        "/stats/{noderef_id}/material-type",
        response_model=dict,
        status_code=HTTP_200_OK,
        tags=["Statistics"],
    )
    async def material_counts_by_type(
        *,
        noderef_id: UUID = Depends(portal_id_param),
        response: Response,
    ):
        material_counts = await crud_stats.material_counts_by_type(
            root_noderef_id=noderef_id
        )

        response.headers["X-Total-Count"] = str(len(material_counts))
        response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
        return material_counts

    @router.get(
        "/collections/{noderef_id}/stats/descendant-collections-materials-counts",
        response_model=List[CollectionMaterialsCount],
        status_code=HTTP_200_OK,
        responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
        tags=["Statistics"],
    )
    async def material_counts_tree(
        *,
        noderef_id: UUID = Depends(portal_id_with_root_param),
        response: Response,
    ):
        descendant_collections = await crud_collection.get_many(
            ancestor_id=noderef_id,
            source_fields={
                CollectionAttribute.NODEREF_ID,
                CollectionAttribute.PATH,
                CollectionAttribute.TITLE,
            },
        )
        materials_counts = await crud_collection.material_counts_by_descendant(
            ancestor_id=noderef_id,
        )

        descendant_collections = {
            collection.noderef_id: collection.title
            for collection in descendant_collections
        }
        stats = []
        errors = []
        for record in materials_counts.results:
            try:
                title = descendant_collections.pop(record.noderef_id)
            except KeyError:
                errors.append(record.noderef_id)
                continue

            stats.append(
                CollectionMaterialsCount(
                    noderef_id=record.noderef_id,
                    title=title,
                    materials_count=record.materials_count,
                )
            )

        stats = [
            *[
                CollectionMaterialsCount(
                    noderef_id=noderef_id,
                    title=title,
                    materials_count=0,
                )
                for (noderef_id, title) in descendant_collections.items()
            ],
            *stats,
        ]

        response.headers["X-Total-Count"] = str(len(stats))
        response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
        return stats


def score_modulator_param(
    *, score_modulator: Optional[ScoreModulator] = Query(None)
) -> ScoreModulator:
    return score_modulator


def score_weights_param(
    *, score_weights: Optional[ScoreWeights] = Query(None)
) -> ScoreWeights:
    return score_weights


@router.get(
    "/collections/{noderef_id}/stats/score",
    response_model=ScoreOutput,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Statistics"],
)
async def score(
    *,
    noderef_id: UUID = Depends(portal_id_param),
    response: Response,
):
    score_modulator = ScoreModulator.LINEAR
    score_weights = ScoreWeights.UNIFORM

    collection_stats = await crud_stats.run_stats_score(
        noderef_id=noderef_id, resource_type=ResourceType.COLLECTION
    )

    collection_scores = calc_scores(
        stats=collection_stats, score_modulator=score_modulator
    )

    material_stats = await crud_stats.run_stats_score(
        noderef_id=noderef_id, resource_type=ResourceType.MATERIAL
    )

    material_scores = calc_scores(stats=material_stats, score_modulator=score_modulator)

    score_ = calc_weighted_score(
        collection_scores=collection_scores,
        material_scores=material_scores,
        score_weights=score_weights,
    )

    response.headers["X-Query-Count"] = str(len(context.get("elastic_queries", [])))
    return {
        "score": score_,
        "collections": {"total": collection_stats["total"], **collection_scores},
        "materials": {"total": material_stats["total"], **material_scores},
    }
