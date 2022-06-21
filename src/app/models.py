from itertools import chain
from typing import TypeVar

from app.elastic.fields import Field, FieldType

_ELASTIC_RESOURCE = TypeVar("_ELASTIC_RESOURCE")
_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS = TypeVar(
    "_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS"
)


# TODO: Refactor! This code cannot be refactored or indexed properly, right now. Reduce complexity, e.g., see field
class ElasticResourceAttribute(Field):
    NODEREF_ID = ("nodeRef.id", FieldType.KEYWORD)
    TYPE = ("type", FieldType.KEYWORD)
    NAME = ("properties.cm:name", FieldType.TEXT)
    PERMISSION_READ = ("permissions.Read", FieldType.TEXT)
    EDU_METADATASET = ("properties.cm:edu_metadataset", FieldType.TEXT)
    PROTOCOL = ("nodeRef.storeRef.protocol", FieldType.KEYWORD)
    FULLPATH = ("fullpath", FieldType.KEYWORD)
    KEYWORDS = ("properties.cclom:general_keyword", FieldType.TEXT)
    EDU_CONTEXT = ("properties.ccm:educationalcontext", FieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", FieldType.TEXT)
    REPLICATION_SOURCE_DE = ("replicationsource", FieldType.TEXT)


class _CollectionAttribute(Field):
    TITLE = ("properties.cm:title", FieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", FieldType.TEXT)
    PATH = ("path", FieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", FieldType.KEYWORD)
    NODE_ID = ("nodeRef.id", FieldType.KEYWORD)


CollectionAttribute = Field(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)
