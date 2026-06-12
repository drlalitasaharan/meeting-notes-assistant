"""Add meeting media metadata columns.

Revision ID: 20260612_media_meta
Revises: 20260608_add_user_profile_fields
"""

import sqlalchemy as sa

from alembic import op

revision = "20260612_media_meta"
down_revision = "20260608_add_user_profile_fields"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _columns("meetings")

    if "media_duration_seconds" not in columns:
        op.add_column("meetings", sa.Column("media_duration_seconds", sa.Float(), nullable=True))

    if "media_size_bytes" not in columns:
        op.add_column("meetings", sa.Column("media_size_bytes", sa.BigInteger(), nullable=True))

    if "media_content_type" not in columns:
        op.add_column(
            "meetings", sa.Column("media_content_type", sa.String(length=255), nullable=True)
        )

    if "media_filename" not in columns:
        op.add_column("meetings", sa.Column("media_filename", sa.String(length=255), nullable=True))


def downgrade() -> None:
    columns = _columns("meetings")

    if "media_filename" in columns:
        op.drop_column("meetings", "media_filename")

    if "media_content_type" in columns:
        op.drop_column("meetings", "media_content_type")

    if "media_size_bytes" in columns:
        op.drop_column("meetings", "media_size_bytes")

    if "media_duration_seconds" in columns:
        op.drop_column("meetings", "media_duration_seconds")
