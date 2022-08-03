from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


@dataclass(frozen=True)
class QualityOutput:
    row_header: str
    level: Optional[
        int
    ]  # Needs to be optional since timeline database does not have levels - yet
    columns: dict[str, float]


class QualityOutputModel(BaseModel):
    row_header: str = Field(default="", description="Name of the evaluated metadatum.")
    level: int = Field(default=1, description="Hierarchy level of this metadatum")
    columns: dict[str, float] = Field(
        description="The ratio of quality for the required columns."
    )


class QualityOutputResponse(BaseModel):
    data: list[QualityOutputModel] = Field(
        default=[], description="Quality data per metadatum and column"
    )
    total: dict[str, int] = Field(
        default={}, description="Column names and total materials per column"
    )


Base = declarative_base()


class Timeline(Base):
    __tablename__ = "timeline"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False)
    quality_matrix = Column(JSON, nullable=False)
    form = Column(Text, nullable=False)
    node_id = Column(UUID, nullable=False)
    total = Column(JSON, nullable=False)


class Forms(str, Enum):
    """
    The form of a quality matrix specifies what will be used as grouping.
    It defines the columns and row labels of the table.
    E.g. for REPLICATION_SOURCE, every row will correspond to a specific replication source, and the columns will
    be metadata fields.
    The values in the cells correspond to the percentages of fields that are missing given the replication source
    of the row.
    """

    REPLICATION_SOURCE = "Bezugsquelle"
    COLLECTIONS = "Sammlungen"
