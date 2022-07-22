from datetime import datetime

from pydantic import BaseModel


# TODO: Rename, as used for materials in background_task, as well
class Collection(BaseModel):
    id: str  # TODO: Refactored to UUID
    doc: dict
    derived_at: datetime
