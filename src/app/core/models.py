from itertools import chain

from app.elastic.fields import ElasticField, ElasticFieldType
from app.models import ElasticResourceAttribute


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
        "properties.ccm:oeh_lrt_aggregated",
        ElasticFieldType.TEXT,
    )
    LEARNINGRESOURCE_TYPE_DE = (
        "i18n.de_DE.ccm:oeh_lrt_aggregated",
        ElasticFieldType.TEXT,
    )
    EDUENDUSERROLE_DE = (
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        ElasticFieldType.TEXT,
    )
    CONTAINS_ADS = ("properties.ccm:containsAdvertisement", ElasticFieldType.TEXT)
    OBJECT_TYPE = ("properties.ccm:objecttype", ElasticFieldType.TEXT)


LearningMaterialAttribute = ElasticField(
    "LearningMaterialAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _LearningMaterialAttribute)
    ],
)
