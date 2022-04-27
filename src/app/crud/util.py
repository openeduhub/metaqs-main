from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.sql import ClauseElement
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.models.collection import Collection, PortalTreeNode


class CollectionNotFoundException(HTTPException):
    def __init__(self, noderef_id):
        super().__init__(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Collection with id '{noderef_id}' not found",
        )


class StatsNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_404_NOT_FOUND,
            detail="Stats not found",
        )


class OrderByDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class OrderByParams(BaseModel):
    column: str
    direction: OrderByDirection = OrderByDirection.ASC

    def __call__(self, query: ClauseElement):
        col = query.columns[self.column]
        if self.direction == OrderByDirection.DESC:
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())
        return query


async def build_portal_tree(
    collections: List[Collection], root_noderef_id: UUID
) -> List[PortalTreeNode]:
    lut = {str(root_noderef_id): []}

    for collection in collections:
        portal_node = PortalTreeNode(
            noderef_id=collection.noderef_id,
            title=collection.title,
            children=[],
        )

        try:
            lut[str(collection.parent_id)].append(portal_node)
        except KeyError:
            lut[str(collection.parent_id)] = [portal_node]

        lut[str(collection.noderef_id)] = portal_node.children

    return lut.get(str(root_noderef_id), [])
