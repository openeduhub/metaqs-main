from enum import Enum, auto


class ElasticFieldType(str, Enum):
    KEYWORD = auto()
    TEXT = auto()


class ElasticField(str, Enum):
    def __new__(cls, path: str, field_type: ElasticFieldType):
        obj = str.__new__(cls, [path])
        obj._value_ = path
        obj.path = path
        obj.field_type = field_type
        return obj

    @property
    def keyword(self):
        return f"{self.path}.keyword"


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
