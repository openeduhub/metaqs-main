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
    missing_edu_context: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_object_type: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without object type"
    )
    missing_description: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without description"
    )
    missing_license: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries with missing license"
    )
    missing_keywords: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries without title"
    )
    missing_ads_qualifier: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of entries missing advertisement qualifier",
    )
    missing_subjects: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of entries missing subjects"
    )
    missing_material_type: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of entries missing material type",
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
