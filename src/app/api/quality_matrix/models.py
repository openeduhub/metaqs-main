from pydantic import BaseModel, Field


class ColumnOutputModel(BaseModel):
    metadatum: str = Field(default="", description="Name of the evaluated metadatum.")
    columns: dict[str, float] = Field(
        description="The ratio of quality for the required columns."
    )
