"""Add scheduled_at column to meetings (idempotent).

This migration safely adds the scheduled_at column only if it is missing,
so it can coexist with other branches that already added the column.
"""

import sqlalchemy as sa  # noqa: F401

from alembic import op

# revision identifiers, used by Alembic.
revision = "2033_scheduled_at"  # 👈 <= 32 chars, unique
down_revision = "2032"  # transcripts revision
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'meetings'
                  AND column_name = 'scheduled_at'
            ) THEN
                ALTER TABLE meetings
                ADD COLUMN scheduled_at TIMESTAMP WITHOUT TIME ZONE;
            END IF;
        END$$;
        """
    )


def downgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'meetings'
                  AND column_name = 'scheduled_at'
            ) THEN
                ALTER TABLE meetings
                DROP COLUMN scheduled_at;
            END IF;
        END$$;
        """
    )
