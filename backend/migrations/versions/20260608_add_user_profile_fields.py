"""Add user profile fields

Revision ID: 20260608_add_user_profile_fields
Revises: 2026_add_users_and_meeting_owner
Create Date: 2026-06-08 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260608_add_user_profile_fields"
down_revision = "2026_add_users_and_meeting_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(length=120), nullable=True, server_default=""),
    )
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(length=120), nullable=True, server_default=""),
    )
    op.add_column(
        "users",
        sa.Column("organization_name", sa.String(length=255), nullable=True),
    )

    op.execute("UPDATE users SET first_name = '' WHERE first_name IS NULL")
    op.execute("UPDATE users SET last_name = '' WHERE last_name IS NULL")

    op.alter_column(
        "users",
        "first_name",
        existing_type=sa.String(length=120),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "users",
        "last_name",
        existing_type=sa.String(length=120),
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("users", "organization_name")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
