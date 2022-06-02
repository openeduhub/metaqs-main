from enum import Enum, unique

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pgsql
from sqlalchemy.orm import declarative_base

from app.core.config import DATABASE_URL

engine = sa.create_engine(str(DATABASE_URL), future=True)
Base = declarative_base()


@unique
class ResourceType(Enum):
    COLLECTION = "collection"
    MATERIAL = "material"


@unique
class ResourceField(Enum):
    TITLE = "title"
    DESCRIPTION = "description"
    KEYWORDS = "keywords"
    EDU_CONTEXT = "edu_context"
    TAXON_ID = "taxon_id"
    LEARNING_RESOURCE_TYPE = "learning_resource_type"
    LICENSE = "license"
    ADS_QUALIFIER = "ads_qualifier"
    OBJECT_TYPE = "object_type"
    INTENDED_ENDUSER_ROLE = "intended_enduser_role"
    URL = "url"
    REPLICATION_SOURCE = "replication_source"
    REPLICATION_SOURCE_ID = "replication_source_id"


class Collection(Base):
    __table__ = sa.Table(
        "collections",
        Base.metadata,
        schema="raw",
        autoload_with=engine,
    )


class Material(Base):
    __table__ = sa.Table(
        "materials",
        Base.metadata,
        schema="raw",
        autoload_with=engine,
    )


search_stats = sa.Table(
    "search_stats",
    Base.metadata,
    sa.Column(
        "resource_field", pgsql.ENUM(ResourceField), primary_key=True, nullable=False
    ),
    sa.Column("resource_type", pgsql.ENUM(ResourceType), nullable=False),
    schema="store",
    autoload_with=engine,
)

spellcheck_queue = sa.Table(
    "spellcheck_queue",
    Base.metadata,
    sa.Column(
        "resource_field", pgsql.ENUM(ResourceField), primary_key=True, nullable=False
    ),
    sa.Column("resource_type", pgsql.ENUM(ResourceType), nullable=False),
    schema="staging",
    autoload_with=engine,
)

spellcheck = sa.Table(
    "spellcheck",
    Base.metadata,
    sa.Column(
        "resource_field", pgsql.ENUM(ResourceField), primary_key=True, nullable=False
    ),
    sa.Column("resource_type", pgsql.ENUM(ResourceType), nullable=False),
    schema="store",
    autoload_with=engine,
)
