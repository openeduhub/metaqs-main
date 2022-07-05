from app.elastic.fields import ElasticField, ElasticFieldType


# TODO: distinguish better what ElasticResourceAttribute and CollectionAttribute do, how they differ
#  and why there additional context is meaningful
class ElasticResourceAttribute(ElasticField):
    EDU_CONTEXT = ("properties.ccm:educationalcontext", ElasticFieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", ElasticFieldType.TEXT)
    FULLPATH = ("fullpath", ElasticFieldType.KEYWORD)
    KEYWORDS = ("properties.cclom:general_keyword", ElasticFieldType.TEXT)
    NAME = ("properties.cm:name", ElasticFieldType.TEXT)
    NODEREF_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    REPLICATION_SOURCE_DE = ("replicationsource", ElasticFieldType.TEXT)
    TYPE = ("type", ElasticFieldType.KEYWORD)


class CollectionAttribute(ElasticField):
    DESCRIPTION = ("properties.cm:description", ElasticFieldType.TEXT)
    PARENT_ID = ("parentRef.id", ElasticFieldType.KEYWORD)
    PATH = ("path", ElasticFieldType.KEYWORD)
    NODE_ID = ("nodeRef.id", ElasticFieldType.KEYWORD)
    TITLE = ("properties.cm:title", ElasticFieldType.TEXT)
