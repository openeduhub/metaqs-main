from datetime import datetime

from pydantic import BaseModel, Json


class Collection(BaseModel):
    id: int
    doc: Json
    derived_at: datetime
