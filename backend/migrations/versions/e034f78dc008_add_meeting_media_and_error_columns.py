import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e034f78dc008"
down_revision = "2034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column("raw_media_path", sa.String(), nullable=True),
    )
    op.add_column(
        "meetings",
        sa.Column("last_error", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "meetings",
        sa.Column("source", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meetings", "source")
    op.drop_column("meetings", "last_error")
    op.drop_column("meetings", "raw_media_path")
