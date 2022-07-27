from typing import List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from starlette_context import context

import src.app.crud.collection as crud_collection
import src.app.crud.learning_material as crud_materials
from src.app.api.util import (
    filter_response_fields,
    material_response_fields,
    materials_filter_params,
    portal_id_with_root_param,
)
from src.app.crud import MissingMaterialAttributeFilter
from src.app.models.learning_material import LearningMaterial, LearningMaterialAttribute

router = APIRouter()


@router.get(
    "/stats/material-types",
    response_model=List[str],
    status_code=HTTP_200_OK,
    tags=["Materials"],
)
async def get_material_types(response: Response):
    material_types = await crud_materials.material_types()

    response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
    return material_types


@router.get(
    "/collections/{noderef_id}/pending-materials/{missing_attr}",
    response_model=List[LearningMaterial],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Materials"],
)
async def filter_materials_with_missing_attributes(
    *,
    noderef_id: UUID = Depends(portal_id_with_root_param),
    missing_attr_filter: MissingMaterialAttributeFilter = Depends(
        materials_filter_params
    ),
    response_fields: Optional[Set[LearningMaterialAttribute]] = Depends(
        material_response_fields
    ),
    response: Response,
):
    if response_fields:
        response_fields.add(LearningMaterialAttribute.NODEREF_ID)

    materials = await crud_collection.get_child_materials_with_missing_attributes(
        noderef_id=noderef_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=response_fields,
    )

    response.headers["X-Total-Count"] = str(len(materials))
    response.headers["X-Query-Count"] = str(len(context.get("elastic_queries")))
    return filter_response_fields(materials, response_fields=response_fields)
