# ruff: noqa: I001
"""Add transcripts table

Revision ID: 2032
Revises: 2031
Create Date: 2025-10-12
"""

from alembic import op
import sqlalchemy as sa

revision = "2032"
down_revision = "2031"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("transcripts"):
        op.create_table(
            "transcripts",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column(
                "meeting_id",
                sa.Integer(),
                sa.ForeignKey("meetings.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.create_index("ix_transcripts_meeting_id", "transcripts", ["meeting_id"])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("transcripts"):
        try:
            op.drop_index("ix_transcripts_meeting_id", table_name="transcripts")
        except Exception:
            pass
        op.drop_table("transcripts")
