from pydantic import BaseModel, Field


class MissingCollectionProperties(BaseModel):
    total: int = Field(ge=0, description="Number of entries")
    short_description: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of entries without short description",
    )
    short_title: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without short title"
    )
    missing_edu_context: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_description: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without description"
    )
    few_keywords: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries with few keywords"
    )
    missing_keywords: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without title"
    )


class MissingMaterialProperties(BaseModel):
    total: int = Field(default=0, ge=0, description="Number of entries")
    missing_title: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without title"
    )
    missing_material_type: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of entries missing material type",
    )
    missing_subjects: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries missing subjects"
    )
    missing_url: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without url"
    )
    missing_license: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries with missing license"
    )
    missing_publisher: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without publisher"
    )
    missing_description: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without description"
    )
    missing_intended_end_user_role: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of entries without intended end user role",
    )
    missing_edu_context: float = Field(
        ge=0.0, le=1.0, description="Ratio of entries without edu context"
    )


class ScoreOutput(BaseModel):
    score: int = Field(ge=0, le=100, description="Overall score")
    oer_ratio: int = Field(ge=0, le=100, description="Overall ratio of OER content")
    collections: MissingCollectionProperties = Field(
        description="Score for specific collection properties"
    )
    materials: MissingMaterialProperties = Field(
        description="Score for specific material properties"
    )
