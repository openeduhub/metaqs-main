from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Extra

from app.elastic.dsl import ElasticField, ElasticFieldType


class ElasticResourceAttribute(ElasticField):
    """
    A class representing the data stored in elastic search.
    It describes the currently essential parts of the metadata.

    Elasticsearch mixes attributes of collections and materials, both in the main structure (collections, properties),
    as well as in properties.

    The prefix "cm" indicates data connected to collections and is based on Alfresco.
    "cclom" connects to materials and is based on LOM specification.
    "ccm" is an extension of the Alfresco attributes.

    Beware, none of these has been used strictly, there may be mixing.

    """

    ACCESSIBILITY_FIND = (
        "properties.ccm:oeh_accessibility_find",
        ElasticFieldType.TEXT,
    )
    ACCESSIBILITY_OPEN = (
        "properties.ccm:oeh_accessibility_open",
        ElasticFieldType.TEXT,
    )
    ACCESSIBILITY_SECURITY = (
        "properties.ccm:oeh_accessibility_security",
        ElasticFieldType.TEXT,
    )
    ACCESSIBILITY_SUMMARY = (
        "properties.ccm:accessibilitySummary",
        ElasticFieldType.TEXT,
    )
    AGE_RANGE = ("properties.ccm:educationaltypicalagerange", ElasticFieldType.TEXT)
    AUTHOR = ("properties.ccm:author_freetext", ElasticFieldType.TEXT)
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
    COMPETENCE = ("properties.ccm:competence", ElasticFieldType.TEXT)
    COMPETENCE_CHECK = ("properties.ccm:oeh_competence_check", ElasticFieldType.TEXT)
    COMPETENCE_REQUIREMENTS = (
        "properties.ccm:oeh_competence_requirements",
        ElasticFieldType.TEXT,
    )
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", ElasticFieldType.TEXT)
    CONTENT_FULLTEXT = ("content.fulltext", ElasticFieldType.TEXT)
    COVER = ("preview", ElasticFieldType.TEXT)
    CREATED = ("properties.cm:created", ElasticFieldType.TEXT)
    CURRICULUM = ("properties.ccm:curriculum", ElasticFieldType.TEXT)
    DESCRIPTION = ("properties.cclom:general_description", ElasticFieldType.TEXT)
    DURATION = ("properties.cclom:duration", ElasticFieldType.TEXT)
    EDITORIAL_FILE_TYPE = ("virtual:editorial_file_type", ElasticFieldType.TEXT)
    EDITORIAL_PUBLISHER = (
        "properties.virtual:editorial_publisher",
        ElasticFieldType.TEXT,
    )
    EDU_CONTEXT = ("properties.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_ENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        ElasticFieldType.TEXT,
    )
    EDU_METADATASET = ("properties.cm:edu_metadataset", ElasticFieldType.TEXT)
    FEEDBACK = ("properties.feedback_comment", ElasticFieldType.TEXT)
    FSK = ("properties.ccm:fskRating", ElasticFieldType.KEYWORD)
    FULLPATH = ("fullpath", ElasticFieldType.KEYWORD)
    INTEROPERABILITY = ("properties.ccm:oeh_interoperability", ElasticFieldType.TEXT)
    KEYWORDS = ("properties.cclom:general_keyword", ElasticFieldType.TEXT)
    LANGUAGE = ("properties.cclom:general_language", ElasticFieldType.TEXT)
    LANGUAGE_TARGET = ("properties.ccm:oeh_languageTarget", ElasticFieldType.TEXT)
    LEARNINGRESOURCE_TYPE = (
        "properties.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt",
        ElasticFieldType.TEXT,
    )
    LEARNING_TIME = (
        "properties.cclom:typicallearningtime",
        ElasticFieldType.TEXT,
    )
    LICENSED_UNTIL = ("properties.ccm:license_to", ElasticFieldType.TEXT)
    LICENSES = ("properties.ccm:commonlicense_key", ElasticFieldType.TEXT)

    LOGIN = ("properties.ccm:oeh_quality_login", ElasticFieldType.TEXT)

    METADATA_CONTRIBUTER_CREATOR = (
        "properties.ccm:metadatacontributer_creator",
        ElasticFieldType.TEXT,
    )
    METADATA_CONTRIBUTER_VALIDATOR = (
        "properties.ccm:metadatacontributer_validator",
        ElasticFieldType.TEXT,
    )
    METADATA_CONTRIBUTER_PROVIDER = (
        "properties.ccm:metadatacontributer_provider",
        ElasticFieldType.TEXT,
    )
    MIMETYPE = ("content.mimetype", ElasticFieldType.TEXT)
    MODIFIED = ("properties.cm:modified", ElasticFieldType.TEXT)
    NAME = ("properties.cm:name", ElasticFieldType.TEXT)
    NODE_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    OBJECT_TYPE = ("properties.ccm:objecttype", ElasticFieldType.TEXT)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)
    PATH = ("path", ElasticFieldType.KEYWORD)
    PERMISSION_READ = ("permissions.Read", ElasticFieldType.TEXT)
    PRICE = ("properties.ccm:price", ElasticFieldType.TEXT)
    PROTOCOL = ("nodeRef.storeRef.protocol", ElasticFieldType.KEYWORD)
    PUBLISHED = ("properties.ccm:published_date", ElasticFieldType.TEXT)
    PUBLISHER = ("properties.ccm:oeh_publisher_combined", ElasticFieldType.TEXT)
    PUBLISHING = (
        "properties.ccm:lifecyclecontributer_publisher",
        ElasticFieldType.TEXT,
    )

    PUBLISHER_HANDLE = ("properties.ccm:published_handle_id", ElasticFieldType.TEXT)
    QUALITY_COPYRIGHT_LAW = (
        "properties.ccm:oeh_quality_copyright_law",
        ElasticFieldType.TEXT,
    )
    QUALITY_CORRECTNESS = (
        "properties.ccm:oeh_quality_correctness",
        ElasticFieldType.TEXT,
    )
    QUALITY_CRIMINAL_LAW = (
        "properties.ccm:oeh_quality_criminal_law",
        ElasticFieldType.TEXT,
    )
    QUALITY_CURRENTNESS = (
        "properties.ccm:oeh_quality_currentness",
        ElasticFieldType.TEXT,
    )
    QUALITY_DATA_PRIVACY = (
        "properties.ccm:oeh_quality_data_privacy",
        ElasticFieldType.TEXT,
    )
    QUALITY_DIAGNOSTICS = (
        "properties.ccm:oeh_quality_didactics",
        ElasticFieldType.TEXT,
    )
    QUALITY_LANGUAGE = ("properties.ccm:oeh_quality_language", ElasticFieldType.TEXT)
    QUALITY_MEDIAL = ("properties.ccm:oeh_quality_medial", ElasticFieldType.TEXT)
    QUALITY_NEUTRALNESS = (
        "properties.ccm:oeh_quality_neutralness",
        ElasticFieldType.TEXT,
    )
    QUALITY_PERSONAL_LAW = (
        "properties.ccm:oeh_quality_personal_law",
        ElasticFieldType.TEXT,
    )
    QUALITY_PROTECTION_OF_MINORS = (
        "properties.ccm:oeh_quality_protection_of_minors",
        ElasticFieldType.TEXT,
    )
    QUALITY_TRANSPARENTNESS = (
        "properties.ccm:oeh_quality_transparentness",
        ElasticFieldType.TEXT,
    )

    REPLICATION_SOURCE = ("properties.ccm:replicationsource", ElasticFieldType.TEXT)
    REPLICATION_SOURCE_DE = ("replicationsource", ElasticFieldType.TEXT)
    SIGNATURES = ("properties.ccm:oeh_signatures", ElasticFieldType.TEXT)
    STATUS = ("properties.cclom:status", ElasticFieldType.TEXT)
    SUBJECTS = ("properties.ccm:taxonid", ElasticFieldType.TEXT)
    SUBJECTS_DE = ("i18n.de_DE.ccm:taxonid", ElasticFieldType.TEXT)
    SYSTEM_ID = ("properties.sys:node-uuid", ElasticFieldType.TEXT)
    TITLE = ("properties.cclom:title", ElasticFieldType.TEXT)
    TYPE = ("type", ElasticFieldType.KEYWORD)
    USABILITY = ("properties.ccm:oeh_usability", ElasticFieldType.TEXT)

    VERSION = ("properties.cm:versionLabel", ElasticFieldType.TEXT)
    WWW_URL = ("properties.ccm:wwwurl", ElasticFieldType.TEXT)


class ResponseConfig:
    allow_population_by_field_name = True
    extra = Extra.ignore


class ResponseModel(BaseModel):
    class Config(ResponseConfig):
        pass


@dataclass(frozen=True)
class SortNode:
    __slots__ = "title", "path", "children"
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
    SortNode(
        title="Pädagogisch",
        children=[
            SortNode(
                path=ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
                children=[],
                title="intended_end_user_role",
            ),
            SortNode(
                path=ElasticResourceAttribute.CURRICULUM,
                children=[],
                title="curriculum",
            ),
            SortNode(
                path=ElasticResourceAttribute.LEARNING_TIME,
                children=[],
                title="learning_time",
            ),
            SortNode(
                path=ElasticResourceAttribute.DURATION, children=[], title="duration"
            ),
            SortNode(
                path=ElasticResourceAttribute.LANGUAGE_TARGET,
                children=[],
                title="language_target",
            ),
            SortNode(
                path=ElasticResourceAttribute.COMPETENCE,
                children=[],
                title="competence",
            ),
            SortNode(
                path=ElasticResourceAttribute.COMPETENCE_REQUIREMENTS,
                children=[],
                title="competence_requirements",
            ),
            SortNode(
                path=ElasticResourceAttribute.COMPETENCE_CHECK,
                children=[],
                title="mimetype",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Rechtliche Unauffälligkeit",
        children=[
            SortNode(
                path=ElasticResourceAttribute.QUALITY_CRIMINAL_LAW,
                children=[],
                title="oeh_quality_criminal_law",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_COPYRIGHT_LAW,
                children=[],
                title="oeh_quality_copyright_law",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_PROTECTION_OF_MINORS,
                children=[],
                title="oeh_quality_protection_of_minors",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_PERSONAL_LAW,
                children=[],
                title="oeh_quality_personal_law",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_DATA_PRIVACY,
                children=[],
                title="oeh_quality_data_privacy",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Qualität",
        children=[
            SortNode(
                path=ElasticResourceAttribute.QUALITY_CORRECTNESS,
                children=[],
                title="oeh_quality_correctness",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_CURRENTNESS,
                children=[],
                title="oeh_quality_currentness",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_NEUTRALNESS,
                children=[],
                title="oeh_quality_neutralness",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_LANGUAGE,
                children=[],
                title="oeh_quality_language",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_MEDIAL,
                children=[],
                title="oeh_quality_medial",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_DIAGNOSTICS,
                children=[],
                title="oeh_quality_didactics",
            ),
            SortNode(
                path=ElasticResourceAttribute.QUALITY_TRANSPARENTNESS,
                children=[],
                title="oeh_quality_transparentness",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Zugänglichkeit",
        children=[
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_OPEN,
                children=[],
                title="oeh_accessibility_open",
            ),
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_FIND,
                children=[],
                title="oeh_accessibility_find",
            ),
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_SUMMARY,
                children=[],
                title="accessibilitySummary",
            ),
            SortNode(
                path=ElasticResourceAttribute.USABILITY,
                children=[],
                title="oeh_usability",
            ),
            SortNode(
                path=ElasticResourceAttribute.INTEROPERABILITY,
                children=[],
                title="oeh_interoperability",
            ),
            SortNode(path=ElasticResourceAttribute.PRICE, children=[], title="price"),
            SortNode(
                path=ElasticResourceAttribute.LOGIN,
                children=[],
                title="oeh_quality_login",
            ),
            SortNode(
                path=ElasticResourceAttribute.ACCESSIBILITY_SECURITY,
                children=[],
                title="oeh_accessibility_security",
            ),
            SortNode(
                path=ElasticResourceAttribute.LICENSED_UNTIL,
                children=[],
                title="license_to",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Lizenz, Quelle, Mitwirkende",
        children=[
            SortNode(
                path=ElasticResourceAttribute.LICENSES, children=[], title="license"
            ),
            SortNode(
                path=ElasticResourceAttribute.AUTHOR,
                children=[],
                title="author_freetext",
            ),
            SortNode(
                path=ElasticResourceAttribute.EDITORIAL_PUBLISHER,
                children=[],
                title="editorial_publisher",
            ),
            SortNode(
                path=ElasticResourceAttribute.PUBLISHED,
                children=[],
                title="published_date",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Entstehung des Inhaltes",
        children=[
            SortNode(
                path=ElasticResourceAttribute.PUBLISHING,
                children=[],
                title="publishing",
            ),
            SortNode(
                path=ElasticResourceAttribute.CREATED, children=[], title="created"
            ),
            SortNode(
                path=ElasticResourceAttribute.MODIFIED, children=[], title="modified"
            ),
            SortNode(
                path=ElasticResourceAttribute.VERSION, children=[], title="versionLabel"
            ),
            SortNode(
                path=ElasticResourceAttribute.PUBLISHER, children=[], title="publisher"
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Identifier und Signaturen",
        children=[
            SortNode(
                path=ElasticResourceAttribute.SYSTEM_ID, children=[], title="node_uuid"
            ),
            SortNode(
                path=ElasticResourceAttribute.PUBLISHER_HANDLE,
                children=[],
                title="published_handle_id",
            ),
            SortNode(
                path=ElasticResourceAttribute.SIGNATURES,
                children=[],
                title="oeh_signatures",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Nutzung und Bewertung",
        children=[
            SortNode(
                path=ElasticResourceAttribute.FEEDBACK,
                children=[],
                title="feedback_comment",
            ),
        ],
        path=None,
    ),
    SortNode(
        title="Erschließung und Kuratierung",
        children=[
            SortNode(
                path=ElasticResourceAttribute.METADATA_CONTRIBUTER_CREATOR,
                children=[],
                title="creator",
            ),
            SortNode(
                path=ElasticResourceAttribute.METADATA_CONTRIBUTER_PROVIDER,
                children=[],
                title="provider",
            ),
            SortNode(
                path=ElasticResourceAttribute.METADATA_CONTRIBUTER_VALIDATOR,
                children=[],
                title="validator",
            ),
        ],
        path=None,
    ),
]

required_collection_properties = {
    child.path.path: child.title
    for node in metadata_hierarchy
    for child in node.children
}
oer_license = ["CC_0", "PDM", "CC_BY", "CC_BY_SA"]
