"""Add meetings table

Revision ID: 2031
Revises: 0002
Create Date: 2025-10-12
"""

from alembic import op
import sqlalchemy as sa

# --- Alembic identifiers ---
revision = "2031"
down_revision = "0002"          # If you need it in your chain, set this to the prior rev (e.g., "0000" or "0001")
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Be idempotent: only create if missing (avoids "table already exists")
    if not insp.has_table("meetings"):
        op.create_table(
            "meetings",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("scheduled_at", sa.DateTime(), nullable=True),
            sa.Column("agenda", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'new'")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        # Optional explicit index (SQLite often indexes PK automatically; keep if you had it originally)
        op.create_index("ix_meetings_id", "meetings", ["id"])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("meetings"):
        # Drop the optional explicit index first if it exists
        try:
            op.drop_index("ix_meetings_id", table_name="meetings")
        except Exception:
            # index may not exist on all backends
            pass
        op.drop_table("meetings")
