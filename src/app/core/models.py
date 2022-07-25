from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, Extra

from app.elastic.dsl import ElasticField, ElasticFieldType


class ElasticResourceAttribute(ElasticField):
    COLLECTION_DESCRIPTION = ("properties.cm:description", ElasticFieldType.TEXT)
    COLLECTION_NODEREF_ID = ("collections.nodeRef.id", ElasticFieldType.TEXT)
    COLLECTION_PATH = ("collections.path", ElasticFieldType.TEXT)
    COLLECTION_TITLE = ("properties.cm:title", ElasticFieldType.TEXT)
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", ElasticFieldType.TEXT)
    CONTENT_FULLTEXT = ("content.fulltext", ElasticFieldType.TEXT)
    COVER = ("preview", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cclom:general_description", ElasticFieldType.TEXT)
    EDU_CONTEXT = ("properties.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDUENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        ElasticFieldType.TEXT,
    )
    EDU_METADATASET = ("properties.cm:edu_metadataset", ElasticFieldType.TEXT)
    FULLPATH = ("fullpath", ElasticFieldType.KEYWORD)
    KEYWORDS = ("properties.cclom:general_keyword", ElasticFieldType.TEXT)
    LEARNINGRESOURCE_TYPE = (
        "properties.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LICENSES = ("properties.ccm:commonlicense_key", ElasticFieldType.TEXT)
    NAME = ("properties.cm:name", ElasticFieldType.TEXT)
    NODE_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    OBJECT_TYPE = ("properties.ccm:objecttype", ElasticFieldType.TEXT)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)
    PATH = ("path", ElasticFieldType.KEYWORD)
    PERMISSION_READ = ("permissions.Read", ElasticFieldType.TEXT)
    PROTOCOL = ("nodeRef.storeRef.protocol", ElasticFieldType.KEYWORD)
    PUBLISHER = ("properties.ccm:oeh_publisher_combined", ElasticFieldType.TEXT)
    REPLICATION_SOURCE_DE = ("replicationsource", ElasticFieldType.TEXT)
    SUBJECTS = ("properties.ccm:taxonid", ElasticFieldType.TEXT)
    SUBJECTS_DE = ("i18n.de_DE.ccm:taxonid", ElasticFieldType.TEXT)
    TITLE = ("properties.cclom:title", ElasticFieldType.TEXT)
    TYPE = ("type", ElasticFieldType.KEYWORD)
    WWW_URL = ("properties.ccm:wwwurl", ElasticFieldType.TEXT)


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass


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
            ElasticResourceAttribute.TITLE,
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


required_collection_properties = {
    ElasticResourceAttribute.TITLE.path: "title",
    ElasticResourceAttribute.LEARNINGRESOURCE_TYPE.path: "learning_resource_type",
    ElasticResourceAttribute.SUBJECTS.path: "taxon_id",
    ElasticResourceAttribute.WWW_URL.path: "url",
    ElasticResourceAttribute.LICENSES.path: "license",
    ElasticResourceAttribute.PUBLISHER.path: "publisher",
    ElasticResourceAttribute.DESCRIPTION.path: "description",
    ElasticResourceAttribute.EDUENDUSERROLE_DE.path: "intended_end_user_role",
    ElasticResourceAttribute.EDU_CONTEXT.path: "edu_context",
    ElasticResourceAttribute.COVER.path: "cover",
}


_ELASTIC_RESOURCE = TypeVar("_ELASTIC_RESOURCE")
_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS = TypeVar(
    "_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS"
)
