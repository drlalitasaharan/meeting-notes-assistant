"""add confidential mode fields

Revision ID: 20260630_confidential_mode_v1
Revises: 20260625_processing_obs
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260630_confidential_mode_v1"
down_revision = "20260625_processing_obs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column(
            "confidential_mode",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "meetings",
        sa.Column("recording_retention_policy", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "meetings",
        sa.Column("recording_deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "meetings",
        sa.Column(
            "recording_delete_status",
            sa.String(length=40),
            nullable=False,
            server_default="not_required",
        ),
    )
    op.add_column(
        "meetings",
        sa.Column("recording_delete_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_meetings_confidential_mode",
        "meetings",
        ["confidential_mode"],
    )
    op.create_index(
        "ix_meetings_recording_delete_status",
        "meetings",
        ["recording_delete_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_meetings_recording_delete_status", table_name="meetings")
    op.drop_index("ix_meetings_confidential_mode", table_name="meetings")
    op.drop_column("meetings", "recording_delete_error")
    op.drop_column("meetings", "recording_delete_status")
    op.drop_column("meetings", "recording_deleted_at")
    op.drop_column("meetings", "recording_retention_policy")
    op.drop_column("meetings", "confidential_mode")
