import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7cb9db845fc3"
down_revision = "e034f78dc008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meeting_id", sa.String(), nullable=False),
        sa.Column("raw_transcript", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_points", sa.JSON(), nullable=True),
        sa.Column("action_items", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("meeting_notes")
