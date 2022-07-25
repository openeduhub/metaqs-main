from dataclasses import dataclass
from itertools import chain
from typing import TypeVar

from pydantic import BaseModel, Extra

from app.elastic.dsl import ElasticField, ElasticFieldType

# TODO: distinguish better what ElasticResourceAttribute and CollectionAttribute do, how they differ
#  and why their additional context is meaningful.
#  Bring together with LearningMaterialAttribute


class _LearningMaterialAttribute(ElasticField):
    TITLE = ("properties.cclom:title", ElasticFieldType.TEXT)
    SUBJECTS = ("properties.ccm:taxonid", ElasticFieldType.TEXT)
    SUBJECTS_DE = ("i18n.de_DE.ccm:taxonid", ElasticFieldType.TEXT)
    WWW_URL = ("properties.ccm:wwwurl", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cclom:general_description", ElasticFieldType.TEXT)
    LICENSES = ("properties.ccm:commonlicense_key", ElasticFieldType.TEXT)
    COLLECTION_NODEREF_ID = ("collections.nodeRef.id", ElasticFieldType.TEXT)
    COLLECTION_PATH = ("collections.path", ElasticFieldType.TEXT)
    CONTENT_FULLTEXT = ("content.fulltext", ElasticFieldType.TEXT)
    LEARNINGRESOURCE_TYPE = (
        "properties.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    EDUENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        ElasticFieldType.TEXT,
    )
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", ElasticFieldType.TEXT)
    OBJECT_TYPE = ("properties.ccm:objecttype", ElasticFieldType.TEXT)
    PUBLISHER = ("properties.ccm:oeh_publisher_combined", ElasticFieldType.TEXT)
    COVER = ("preview", ElasticFieldType.TEXT)


class ElasticResourceAttribute(ElasticField):
    EDU_CONTEXT = ("properties.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_METADATASET = ("properties.cm:edu_metadataset", ElasticFieldType.TEXT)
    FULLPATH = ("fullpath", ElasticFieldType.KEYWORD)
    KEYWORDS = ("properties.cclom:general_keyword", ElasticFieldType.TEXT)
    NAME = ("properties.cm:name", ElasticFieldType.TEXT)
    NODEREF_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    PERMISSION_READ = ("permissions.Read", ElasticFieldType.TEXT)
    PROTOCOL = ("nodeRef.storeRef.protocol", ElasticFieldType.KEYWORD)
    REPLICATION_SOURCE_DE = ("replicationsource", ElasticFieldType.TEXT)
    TYPE = ("type", ElasticFieldType.KEYWORD)


LearningMaterialAttribute = ElasticField(
    "LearningMaterialAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _LearningMaterialAttribute)
    ],
)


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass


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
    LearningMaterialAttribute.COVER.path: "cover",
}


@dataclass
class SortNode:
    title: str
    children: list[str]


desired_sorting: list[SortNode] = [
    SortNode(
        title="Beschreibendes",
        children=[
            "preview",
            "ccm:collectionshorttitle",
            "cclom:title",
            "cclom:general_description",
            "cclom:status",
            "ccm:wwwurl",
            "cclom:general_language",
        ],
    ),
    SortNode(
        title="Typisierung",
        children=[
            "ccm:oeh_lrt",
            "mimetype",
            "virtual:editorial_file_type",
            "ccm:educationalcontext",
            "ccm:educationaltypicalagerange",
            "ccm:fskRating",
            "ccm:taxonid",
            "cclom:classification_keyword",
            "cclom:general_keyword",
        ],
    ),
    SortNode(
        title="Pädagogisch",
        children=[
            "ccm:educationalintendedenduserrole",
            "ccm:curriculum",
            "cclom:typicallearningtime",
            "cclom:duration",
            "ccm:oeh_languageTarget",
            "ccm:oeh_competence_requirements",
            "ccm:competence",
            "ccm:oeh_competence_check",
        ],
    ),
    SortNode(
        title="Rechtliche Unauffälligkeit",
        children=[
            "ccm:oeh_quality_criminal_law",
            "ccm:oeh_quality_copyright_law",
            "ccm:oeh_quality_protection_of_minors",
            "ccm:oeh_quality_personal_law",
            "ccm:oeh_quality_data_privacy",
        ],
    ),
    SortNode(
        title="Qualität",
        children=[
            "ccm:oeh_quality_correctness",
            "ccm:oeh_quality_currentness:",
            "ccm:oeh_quality_neutralness",
            "ccm:oeh_quality_language",
            "ccm:oeh_quality_medial",
            "ccm:oeh_quality_didactics",
            "ccm:oeh_quality_transparentness",
        ],
    ),
    SortNode(
        title="Zugänglichkeit",
        children=[
            "ccm:oeh_accessibility_open",
            "ccm:oeh_accessibility_find",
            "ccm:accessibilitySummary",
            "ccm:oeh_usability",
            "ccm:oeh_interoperability",
            "ccm:containsAdvertisement",
            "ccm:price?",
            "ccm:oeh_quality_login",
            "ccm:oeh_accessibility_security",
            "ccm:license_to",
        ],
    ),
    SortNode(
        title="Lizenz, Quelle, Mitwirkende",
        children=[
            "ccm:commonlicense_key",
            "ccm:author_freetext",
            "virtual:editorial_publisher",
            "ccm:published_date",
            "cm:created",
            "cm:modified",
            "cm:versionLabel",
        ],
    ),
    SortNode(
        title="Identifier und Signaturen",
        children=[
            "sys:node-uuid",
            "ccm:published_handle_id",
            "ccm:oeh_signatures",
        ],
    ),
    SortNode(
        title="Nutzung und Bewertung",
        children=[
            "feedback_comment",
        ],
    ),
]
_ELASTIC_RESOURCE = TypeVar("_ELASTIC_RESOURCE")
_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS = TypeVar(
    "_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS"
)


class CollectionAttribute(ElasticField):
    DESCRIPTION = ("properties.cm:description", ElasticFieldType.TEXT)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)
    PATH = ("path", ElasticFieldType.KEYWORD)
    NODE_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    TITLE = ("properties.cm:title", ElasticFieldType.TEXT)
