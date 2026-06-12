"""add upload ledger

Revision ID: 9fc26ee281f2
Revises: 20260612_media_meta
Create Date: 2026-06-12 23:21:13.977738
"""

import sqlalchemy as sa

from alembic import op

revision = "9fc26ee281f2"
down_revision = "20260612_media_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "upload_ledger" not in tables:
        op.create_table(
            "upload_ledger",
            sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
            sa.Column("user_id", sa.String(length=255), nullable=True),
            sa.Column("account_id", sa.String(length=255), nullable=True),
            sa.Column("meeting_id", sa.String(length=255), nullable=True),
            sa.Column("original_filename", sa.String(length=1024), nullable=True),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("content_type", sa.String(length=255), nullable=True),
            sa.Column("storage_key", sa.String(length=2048), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="started"),
            sa.Column("counted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes("upload_ledger")}

    if "ix_upload_ledger_user_id" not in existing_indexes:
        op.create_index("ix_upload_ledger_user_id", "upload_ledger", ["user_id"])

    if "ix_upload_ledger_account_id" not in existing_indexes:
        op.create_index("ix_upload_ledger_account_id", "upload_ledger", ["account_id"])

    if "ix_upload_ledger_meeting_id" not in existing_indexes:
        op.create_index("ix_upload_ledger_meeting_id", "upload_ledger", ["meeting_id"])

    if "ix_upload_ledger_counted_at" not in existing_indexes:
        op.create_index("ix_upload_ledger_counted_at", "upload_ledger", ["counted_at"])

    if "ix_upload_ledger_status" not in existing_indexes:
        op.create_index("ix_upload_ledger_status", "upload_ledger", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "upload_ledger" in inspector.get_table_names():
        existing_indexes = {index["name"] for index in inspector.get_indexes("upload_ledger")}

        for index_name in [
            "ix_upload_ledger_status",
            "ix_upload_ledger_counted_at",
            "ix_upload_ledger_meeting_id",
            "ix_upload_ledger_account_id",
            "ix_upload_ledger_user_id",
        ]:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="upload_ledger")

        op.drop_table("upload_ledger")
