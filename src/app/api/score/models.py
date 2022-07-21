from pydantic import BaseModel, Field

from app.core.models import LearningMaterialAttribute


class MissingCollectionProperties(BaseModel):
    total: int = Field(default=0, ge=0, description="Number of entries")
    short_description: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of entries without short description",
    )
    short_title: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without short title"
    )
    missing_edu_context: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_description: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without description"
    )
    few_keywords: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries with few keywords"
    )
    missing_keywords: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without title"
    )


class MissingMaterialProperties(BaseModel):
    total: int = Field(default=0, ge=0, description="Number of entries")
    missing_title: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without title"
    )
    missing_material_type: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of entries missing material type",
    )
    missing_subjects: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries missing subjects"
    )
    missing_url: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without url"
    )
    missing_license: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries with missing license"
    )
    missing_publisher: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without publisher"
    )
    missing_description: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without description"
    )
    missing_intended_end_user_role: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of entries without intended end user role",
    )
    missing_edu_context: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without edu context"
    )


class ScoreOutput(BaseModel):
    score: int = Field(default=0, ge=0, le=100, description="Overall score")
    oer_ratio: int = Field(
        default=0, ge=0, le=100, description="Overall ratio of OER content"
    )
    collections: MissingCollectionProperties = Field(
        description="Score for specific collection properties"
    )
    materials: MissingMaterialProperties = Field(
        description="Score for specific material properties"
    )


required_collection_properties = {
    LearningMaterialAttribute.TITLE.path: "title",
    LearningMaterialAttribute.LEARNINGRESOURCE_TYPE.path: "learning_resource_type",
    LearningMaterialAttribute.SUBJECTS.path: "taxon_id",
    LearningMaterialAttribute.WWW_URL.path: "url",
    LearningMaterialAttribute.LICENSES.path: "license",
    LearningMaterialAttribute.PUBLISHER.path: "publisher",
    LearningMaterialAttribute.DESCRIPTION.path: "description",
    LearningMaterialAttribute.EDUENDUSERROLE_DE.path: "intended_end_user_role",
    LearningMaterialAttribute.EDU_CONTEXT.path: "edu_context",
}
