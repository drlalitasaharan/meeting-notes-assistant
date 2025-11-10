# ruff: noqa: I001
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "meeting_id",
            sa.Integer(),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_notes_meeting_id", "notes", ["meeting_id"])
    op.create_index("ix_notes_created_at", "notes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_notes_created_at", table_name="notes")
    op.drop_index("ix_notes_meeting_id", table_name="notes")
    op.drop_table("notes")
