from alembic import op
import sqlalchemy as sa

revision = "2033_add_scheduled_at_to_meetings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meetings", "scheduled_at")
