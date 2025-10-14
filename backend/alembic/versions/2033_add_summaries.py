"""Add summaries table

Revision ID: 2033
Revises: 2032
Create Date: 2025-10-12
"""
from alembic import op
import sqlalchemy as sa

revision = "2033"
down_revision = "2032"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("summaries"):
        op.create_table(
            "summaries",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("meeting_id", sa.Integer(), sa.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False),
            sa.Column("model", sa.String(length=60), nullable=False, server_default=sa.text("'stub'")),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_summaries_meeting_id", "summaries", ["meeting_id"])

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("summaries"):
        try:
            op.drop_index("ix_summaries_meeting_id", table_name="summaries")
        except Exception:
            pass
        op.drop_table("summaries")
