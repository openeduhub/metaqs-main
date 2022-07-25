from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TypeVar

from pydantic import BaseModel, Extra

from app.elastic.dsl import ElasticField, ElasticFieldType


class ElasticResourceAttribute(ElasticField):
    AGE_RANGE = ("properties.ccm:educationaltypicalagerange", ElasticFieldType.TEXT)
    CLASSIFICATION_KEYWORD = (
        "properties.cclom:classification_keyword",
        ElasticFieldType.TEXT,
    )
    COLLECTION_DESCRIPTION = ("properties.cm:description", ElasticFieldType.TEXT)
    COLLECTION_NODEREF_ID = ("collections.nodeRef.id", ElasticFieldType.TEXT)
    COLLECTION_PATH = ("collections.path", ElasticFieldType.TEXT)
    COLLECTION_SHORT_TITLE = (
        "properties.ccm:collectionshorttitle",
        ElasticFieldType.TEXT,
    )
    COLLECTION_TITLE = ("properties.cm:title", ElasticFieldType.TEXT)
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", ElasticFieldType.TEXT)
    CONTENT_FULLTEXT = ("content.fulltext", ElasticFieldType.TEXT)
    COVER = ("preview", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cclom:general_description", ElasticFieldType.TEXT)
    EDITORIAL_FILE_TYPE = ("virtual:editorial_file_type", ElasticFieldType.TEXT)
    EDU_CONTEXT = ("properties.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDUENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        ElasticFieldType.TEXT,
    )
    EDU_METADATASET = ("properties.cm:edu_metadataset", ElasticFieldType.TEXT)
    FSK = ("properties.ccm:fskRating", ElasticFieldType.KEYWORD)
    FULLPATH = ("fullpath", ElasticFieldType.KEYWORD)
    KEYWORDS = ("properties.cclom:general_keyword", ElasticFieldType.TEXT)
    LANGUAGE = ("properties.cclom:general_language", ElasticFieldType.TEXT)
    LEARNINGRESOURCE_TYPE = (
        "properties.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LICENSES = ("properties.ccm:commonlicense_key", ElasticFieldType.TEXT)
    MIMETYPE = ("mimetype", ElasticFieldType.TEXT)
    NAME = ("properties.cm:name", ElasticFieldType.TEXT)
    NODE_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    OBJECT_TYPE = ("properties.ccm:objecttype", ElasticFieldType.TEXT)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)
    PATH = ("path", ElasticFieldType.KEYWORD)
    PERMISSION_READ = ("permissions.Read", ElasticFieldType.TEXT)
    PROTOCOL = ("nodeRef.storeRef.protocol", ElasticFieldType.KEYWORD)
    PUBLISHER = ("properties.ccm:oeh_publisher_combined", ElasticFieldType.TEXT)
    REPLICATION_SOURCE = ("properties.ccm:replicationsource", ElasticFieldType.TEXT)
    REPLICATION_SOURCE_DE = ("replicationsource", ElasticFieldType.TEXT)
    STATUS = ("properties.cclom:status", ElasticFieldType.TEXT)
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
    path: Optional[ElasticResourceAttribute]
    children: list[SortNode]


metadata_hierarchy: list[SortNode] = [
    SortNode(
        title="Beschreibendes",
        children=[
            SortNode(path=ElasticResourceAttribute.COVER, children=[], title="cover"),
            SortNode(
                path=ElasticResourceAttribute.COLLECTION_SHORT_TITLE,
                children=[],
                title="short_title",
            ),
            SortNode(path=ElasticResourceAttribute.TITLE, children=[], title="title"),
            SortNode(
                path=ElasticResourceAttribute.DESCRIPTION,
                children=[],
                title="description",
            ),
            SortNode(path=ElasticResourceAttribute.STATUS, children=[], title="status"),
            SortNode(path=ElasticResourceAttribute.WWW_URL, children=[], title="url"),
            SortNode(
                path=ElasticResourceAttribute.LANGUAGE, children=[], title="language"
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Typisierung",
        children=[
            SortNode(
                path=ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
                children=[],
                title="learning_resource_type",
            ),
            SortNode(
                path=ElasticResourceAttribute.MIMETYPE, children=[], title="mimetype"
            ),
            SortNode(
                path=ElasticResourceAttribute.EDITORIAL_FILE_TYPE,
                children=[],
                title="file_type",
            ),
            SortNode(
                path=ElasticResourceAttribute.EDU_CONTEXT,
                children=[],
                title="edu_context",
            ),
            SortNode(
                path=ElasticResourceAttribute.AGE_RANGE, children=[], title="age_range"
            ),
            SortNode(path=ElasticResourceAttribute.FSK, children=[], title="fsk"),
            SortNode(
                path=ElasticResourceAttribute.SUBJECTS, children=[], title="taxon_id"
            ),
            SortNode(
                path=ElasticResourceAttribute.CLASSIFICATION_KEYWORD,
                children=[],
                title="classification",
            ),
            SortNode(
                path=ElasticResourceAttribute.KEYWORDS,
                children=[],
                title="general_keywords",
            ),
        ],
        path=None,
    ),
]
"""

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
    ),"""


required_collection_properties = {
    child.path.path: child.title
    for node in metadata_hierarchy
    for child in node.children
}

_ELASTIC_RESOURCE = TypeVar("_ELASTIC_RESOURCE")
_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS = TypeVar(
    "_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS"
)
