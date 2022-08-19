from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


class QualityMatrixRow(BaseModel):
    row_header: str = Field(description="Name of the evaluated attribute, e.g., metadatum or collection id.")
    level: int = Field(description="Hierarchy level of this attribute. Only relevant for collections.")
    columns: dict[str, float] = Field(description="The ratio of quality for the required columns.")


class QualityMatrix(BaseModel):
    data: list[QualityMatrixRow] = Field(description="Quality data per column")
    total: dict[str, int] = Field(description="Column names and total materials per column")


Base = declarative_base()


class Timeline(Base):
    """Table will be automatically created at application start time if it does not exist."""

    __tablename__ = "timeline"
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    timestamp = Column(Integer, nullable=False)
    quality = Column(JSON, nullable=False)
    mode = Column(Text, nullable=False)
    node_id = Column(UUID, nullable=False)
    total = Column(JSON, nullable=False)


class Mode(str, Enum):
    """
    The different modes of the quality matrix.
    """

    REPLICATION_SOURCE = "replication_source"
    COLLECTIONS = "collections"
