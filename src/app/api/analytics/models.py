from datetime import datetime

from pydantic import BaseModel


class Collection(BaseModel):
    id: str
    doc: dict
    derived_at: datetime
