"""Add jobs table; idempotent and Postgres-friendly.

This migration is written in raw SQL so it can be safely run even if the
jobstatus enum or jobs table already exist (for example, because of an older
migration).
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2034"
down_revision = "2033"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create enum type only if it does NOT already exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'jobstatus'
            ) THEN
                CREATE TYPE jobstatus AS ENUM (
                    'queued',
                    'running',
                    'succeeded',
                    'failed'
                );
            END IF;
        END$$;
        """
    )

    # 2) Create jobs table only if it does NOT already exist
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id          VARCHAR PRIMARY KEY,
            kind        VARCHAR NOT NULL,
            status      jobstatus NOT NULL DEFAULT 'queued',
            queue       VARCHAR,
            meta        JSONB,
            created_at  TIMESTAMPTZ NOT NULL,
            updated_at  TIMESTAMPTZ NOT NULL
        );
        """
    )


def downgrade():
    # Safe tear-down if you ever downgrade
    op.execute("DROP TABLE IF EXISTS jobs;")
    op.execute("DROP TYPE IF EXISTS jobstatus;")
