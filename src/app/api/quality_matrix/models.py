from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, Integer, MetaData, Table
from sqlalchemy.orm import as_declarative, declared_attr


class ColumnOutputModel(BaseModel):
    metadatum: str = Field(default="", description="Name of the evaluated metadatum.")
    columns: dict[str, float] = Field(
        description="The ratio of quality for the required columns."
    )


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


def timeline_table(meta: MetaData) -> Table:
    return Table(
        "timeline",
        meta,
        Column("id", Integer),
        Column("timestamp", Integer),
        Column("quality_matrix", JSON),
    )


class Timeline(Base):
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False)
    quality_matrix = Column(JSON, nullable=False)
