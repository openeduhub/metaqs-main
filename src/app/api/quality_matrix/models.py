from enum import Enum
from typing import Union

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, Integer, Text
from sqlalchemy.orm import declarative_base


class ColumnOutputModel(BaseModel):
    metadatum: str = Field(default="", description="Name of the evaluated metadatum.")
    columns: dict[str, float] = Field(
        description="The ratio of quality for the required columns."
    )


Base = declarative_base()


class Timeline(Base):
    __tablename__ = "timeline"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False)
    quality_matrix = Column(JSON, nullable=False)
    form = Column(Text, nullable=False)


class Forms(str, Enum):
    REPLICATION_SOURCE = "Bezugsquelle"
    COLLECTIONS = "Sammlungen"


QUALITY_MATRIX_RETURN_TYPE = list[dict[str, Union[str, dict[str, float]]]]
