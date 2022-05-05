from typing import List, Optional, Set
from uuid import UUID

from fastapi import Path, Query
from pydantic import BaseModel
from starlette.responses import Response

import app.crud.collection as crud_collection
from app.core.config import PORTAL_ROOT_ID
from app.crud import (
    MissingCollectionAttributeFilter,
    MissingCollectionField,
    MissingMaterialAttributeFilter,
    MissingMaterialField,
)
from app.elastic.fields import Field
from app.models.collection import CollectionAttribute
from app.models.learning_material import LearningMaterialAttribute


def collection_id_param(
    *,
    collection_id: UUID = Path(..., examples=crud_collection.COLLECTIONS),
) -> UUID:
    return collection_id


def portal_id_with_root_param(
    *,
    noderef_id: UUID = Path(
        ...,
        examples={
            "Alle Fachportale": {"value": PORTAL_ROOT_ID},
            **crud_collection.COLLECTIONS,
        },
    ),
) -> UUID:
    return noderef_id


CollectionResponseField = Field(
    "CollectionAttribute",
    [(f.name, (f.value, f.field_type)) for f in CollectionAttribute],
)


def collection_response_fields(
    *, response_fields: Set[CollectionResponseField] = Query(None)
) -> Set[CollectionAttribute]:
    return response_fields


LearningMaterialResponseField = Field(
    "MaterialAttribute",
    [(f.name, (f.value, f.field_type)) for f in LearningMaterialAttribute],
)


def material_response_fields(
    *, response_fields: Set[LearningMaterialResponseField] = Query(None)
) -> Set[LearningMaterialAttribute]:
    return response_fields


def filter_response_fields(
    items: List[BaseModel], response_fields: Set[Field] = None
) -> List[BaseModel]:
    if response_fields:
        return [
            i.copy(include={f.name.lower() for f in response_fields}) for i in items
        ]
    return items


def collections_filter_params(
    *, missing_attr: MissingCollectionField = Path(...)
) -> MissingCollectionAttributeFilter:
    return MissingCollectionAttributeFilter(attr=missing_attr)


def materials_filter_params(
    *, missing_attr: MissingMaterialField = Path(...)
) -> MissingMaterialAttributeFilter:
    return MissingMaterialAttributeFilter(attr=missing_attr)


# def sort_params(*, _sort: str = Query(None), _order: str = Query(None)):
#     if _sort or _order:
#         return OrderByParams(column=_sort, direction=_order)


def pagination_params(
    *, _start: int = Query(0), _end: int = Query(None), response: Response
):
    return PaginationParams(start=_start, stop=_end, response=response)


class PaginationParams(BaseModel):
    start: int = 0
    stop: Optional[int] = None
    response: Response

    class Config:
        arbitrary_types_allowed = True

    def __call__(self, records: list):
        self.response.headers["X-Total-Count"] = str(len(records))
        return records[self.start : self.stop]
