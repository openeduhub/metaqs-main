"""custom_types

Revision ID: 0002
Revises: 0001
Create Date: 1970-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        create type resource_type as enum (
            'COLLECTION',
            'MATERIAL'
            );

        create type resource_field as enum (
            'TITLE',
            'DESCRIPTION',
            'KEYWORDS',
            'EDU_CONTEXT',
            'TAXON_ID',
            'LEARNING_RESOURCE_TYPE',
            'LICENSE',
            'ADS_QUALIFIER',
            'OBJECT_TYPE',
            'INTENDED_ENDUSER_ROLE',
            'URL',
            'REPLICATION_SOURCE',
            'REPLICATION_SOURCE_ID'
            );

        create type validation_error as enum (
            'TOO_FEW',
            'TOO_SHORT',
            'LACKS_CLARity'
            );
        """
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        """
        drop type if exists validation_error cascade;
        drop type if exists resource_field cascade;
        drop type if exists resource_type cascade;
        """
    )
