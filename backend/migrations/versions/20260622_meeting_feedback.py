"""add meeting feedback

Revision ID: 20260622_meeting_feedback
Revises: 20260618_billing_foundation
Create Date: 2026-06-22
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260622_meeting_feedback"
down_revision = "20260618_billing_foundation"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    if _has_table("meeting_feedback"):
        return

    op.create_table(
        "meeting_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("usefulness", sa.String(length=20), nullable=False),
        sa.Column("most_useful", sa.String(length=40), nullable=False),
        sa.Column("improvement_text", sa.Text(), nullable=True),
        sa.Column("would_use_again", sa.String(length=20), nullable=False),
        sa.Column("meeting_type", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "meeting_id", name="uq_meeting_feedback_user_meeting"),
    )
    op.create_index(op.f("ix_meeting_feedback_id"), "meeting_feedback", ["id"], unique=False)
    op.create_index(
        op.f("ix_meeting_feedback_meeting_id"),
        "meeting_feedback",
        ["meeting_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_meeting_feedback_user_id"),
        "meeting_feedback",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    if not _has_table("meeting_feedback"):
        return

    op.drop_index(op.f("ix_meeting_feedback_user_id"), table_name="meeting_feedback")
    op.drop_index(op.f("ix_meeting_feedback_meeting_id"), table_name="meeting_feedback")
    op.drop_index(op.f("ix_meeting_feedback_id"), table_name="meeting_feedback")
    op.drop_table("meeting_feedback")
