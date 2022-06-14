from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel


class CollectionNode(BaseModel):
    noderef_id: UUID
    title: Union[str, None]  # might be none due to data model
    children: list[CollectionNode]
    parent_id: Optional[UUID]
