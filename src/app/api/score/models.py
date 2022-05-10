from itertools import chain

from pydantic import BaseModel, Field

from app.elastic.fields import Field as ElasticField
from app.elastic.fields import FieldType
from app.models.elastic import ElasticResourceAttribute


class _CollectionAttribute(ElasticField):
    TITLE = ("properties.cm:title", FieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", FieldType.TEXT)
    PATH = ("path", FieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", FieldType.KEYWORD)


CollectionAttribute = ElasticField(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)


class _LearningMaterialAttribute(ElasticField):
    TITLE = ("properties.cclom:title", FieldType.TEXT)
    SUBJECTS = ("properties.ccm:taxonid", FieldType.TEXT)
    SUBJECTS_DE = ("i18n.de_DE.ccm:taxonid", FieldType.TEXT)
    WWW_URL = ("properties.ccm:wwwurl", FieldType.TEXT)
    DESCRIPTION = ("properties.cclom:general_description", FieldType.TEXT)
    LICENSES = ("properties.ccm:commonlicense_key", FieldType.TEXT)
    COLLECTION_NODEREF_ID = ("collections.nodeRef.id", FieldType.TEXT)
    COLLECTION_PATH = ("collections.path", FieldType.TEXT)
    CONTENT_FULLTEXT = ("content.fulltext", FieldType.TEXT)
    LEARNINGRESOURCE_TYPE = (
        "properties.ccm:oeh_lrt_aggregated",
        FieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt_aggregated",
        FieldType.TEXT,
    )
    EDUENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        FieldType.TEXT,
    )
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", FieldType.TEXT)
    OBJECT_TYPE = ("properties.ccm:objecttype", FieldType.TEXT)


LearningMaterialAttribute = ElasticField(
    "LearningMaterialAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _LearningMaterialAttribute)
    ],
)


class MissingCollectionProperties(BaseModel):
    total: int = Field(default=0, gt=0, description="Number of entries")
    short_description: float = Field(
        default=0.0,
        gt=0.0,
        le=1.0,
        description="Ratio of entries without short description",
    )
    short_title: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without short title"
    )
    missing_edu_context: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_description: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without description"
    )
    few_keywords: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries with few keywords"
    )
    missing_keywords: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without title"
    )


class MissingMaterialProperties(BaseModel):
    total: int = Field(default=0, gt=0, description="Number of entries")
    missing_edu_context: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without edu context"
    )
    missing_object_type: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without object type"
    )
    missing_description: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without description"
    )
    missing_license: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries with missing license"
    )
    missing_keywords: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without keywords"
    )
    missing_title: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries without title"
    )
    missing_ads_qualifier: float = Field(
        default=0.0,
        gt=0.0,
        le=1.0,
        description="Ratio of entries missing advertisement qualifier",
    )
    missing_subjects: float = Field(
        default=0.0, gt=0.0, le=1.0, description="Ratio of entries missing subjects"
    )
    missing_material_type: float = Field(
        default=0.0,
        gt=0.0,
        le=1.0,
        description="Ratio of entries missing material type",
    )


class ScoreOutput(BaseModel):
    score: int = Field(default=0, gt=0, le=100, description="Overall score")
    collections: MissingCollectionProperties = Field(
        description="Score for specific collection properties"
    )
    materials: MissingMaterialProperties = Field(
        description="Score for specific material properties"
    )
