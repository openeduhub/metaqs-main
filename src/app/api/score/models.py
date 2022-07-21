from pydantic import BaseModel, Field


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
    "properties.cclom:title": "title",
    "properties.cclom:general_description": "description",
    "properties.cclom:general_keyword": "keywords",
    "properties.ccm:taxonid": "taxon_id",
    "properties.ccm:educationalcontext": "edu_context",
    "properties.ccm:commonlicense_key": "license",
    "properties.ccm:objecttype": "object_type",
    "properties.ccm:containsAdvertisement": "ads_qualifier",
    "properties.cclom:oeh_lrt_aggregated": "learning_resource_type",
}
