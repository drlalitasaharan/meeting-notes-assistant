"""add processing observability fields

Revision ID: 20260625_processing_obs
Revises: 20260622_meeting_feedback
Create Date: 2026-06-25
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260625_processing_obs"
down_revision = "20260622_meeting_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meetings", sa.Column("processing_stage", sa.String(length=40), nullable=True))
    op.add_column(
        "meetings", sa.Column("processing_error_code", sa.String(length=80), nullable=True)
    )
    op.add_column(
        "meetings", sa.Column("processing_error_message", sa.String(length=500), nullable=True)
    )
    op.add_column("meetings", sa.Column("processing_diagnostics", sa.Text(), nullable=True))
    op.add_column(
        "meetings",
        sa.Column("processing_attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("meetings", sa.Column("processing_timings", sa.JSON(), nullable=True))
    op.create_index("ix_meetings_processing_stage", "meetings", ["processing_stage"])


def downgrade() -> None:
    op.drop_index("ix_meetings_processing_stage", table_name="meetings")
    op.drop_column("meetings", "processing_timings")
    op.drop_column("meetings", "processing_attempts")
    op.drop_column("meetings", "processing_diagnostics")
    op.drop_column("meetings", "processing_error_message")
    op.drop_column("meetings", "processing_error_code")
    op.drop_column("meetings", "processing_stage")
