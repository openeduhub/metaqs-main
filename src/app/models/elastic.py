from typing import ClassVar, Dict, Optional, Type, TypeVar
from uuid import UUID

from glom import Coalesce, glom
from pydantic import Extra

from app.elastic.fields import Field, FieldType

from .base import BaseModel
from .util import EmptyStrToNone

_ELASTIC_RESOURCE = TypeVar("_ELASTIC_RESOURCE")
_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS = TypeVar(
    "_DESCENDANT_COLLECTIONS_MATERIALS_COUNTS"
)


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


class ElasticConfig:
    allow_population_by_field_name = True
    extra = Extra.allow


class ElasticResource(BaseModel):
    noderef_id: UUID
    type: Optional[EmptyStrToNone] = None
    name: Optional[EmptyStrToNone] = None

    source_fields: ClassVar[set] = {
        ElasticResourceAttribute.NODEREF_ID,
        ElasticResourceAttribute.TYPE,
        ElasticResourceAttribute.NAME,
    }

    class Config(ElasticConfig):
        pass

    @classmethod
    def parse_elastic_hit_to_dict(
        cls: Type[_ELASTIC_RESOURCE],
        hit: Dict,
    ) -> dict:
        spec = {
            "noderef_id": ElasticResourceAttribute.NODEREF_ID.path,
            "type": Coalesce(ElasticResourceAttribute.TYPE.path, default=None),
            "name": Coalesce(ElasticResourceAttribute.NAME.path, default=None),
        }
        return glom(hit, spec)

    @classmethod
    def parse_elastic_hit(
        cls: Type[_ELASTIC_RESOURCE],
        hit: Dict,
    ) -> _ELASTIC_RESOURCE:
        return cls.construct(**cls.parse_elastic_hit_to_dict(hit))
