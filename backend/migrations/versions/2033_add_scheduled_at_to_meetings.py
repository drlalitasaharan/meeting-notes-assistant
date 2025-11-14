import sqlalchemy as sa

from alembic import op

# Adjust these if your repo uses different IDs
revision = "2033_add_scheduled_at_to_meetings"
down_revision = "2032_add_transcripts"  # make sure this matches your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meetings", "scheduled_at")
