"""add meeting notes v3 fields

Revision ID: 60ead020d973
Revises: dbd7b21aa1fa
Create Date: 2026-04-11 23:16:02.189657
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "60ead020d973"
down_revision = "dbd7b21aa1fa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meeting_notes", sa.Column("summary_slots", sa.JSON(), nullable=True))
    op.add_column("meeting_notes", sa.Column("action_item_objects", sa.JSON(), nullable=True))
    op.add_column("meeting_notes", sa.Column("decisions", sa.JSON(), nullable=True))
    op.add_column("meeting_notes", sa.Column("decision_objects", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("meeting_notes", "decision_objects")
    op.drop_column("meeting_notes", "decisions")
    op.drop_column("meeting_notes", "action_item_objects")
    op.drop_column("meeting_notes", "summary_slots")
