from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# Alembic identifiers
revision = "2031_add_jobs_table"
down_revision = None
branch_labels = None
depends_on = None

# Named ENUM type; do not auto-create (we'll create via DO $$)
job_status = pg.ENUM('queued','running','succeeded','failed',
                     name='jobstatus', create_type=False)

def upgrade():
    # Create enum once (idempotent)
    op.execute("""    DO $do$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'jobstatus') THEN
            CREATE TYPE jobstatus AS ENUM ('queued','running','succeeded','failed');
        END IF;
    END $do$;
    """)

    op.create_table(
        'jobs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('input_hash', sa.String(), nullable=False),
        sa.Column('status', job_status, nullable=False, server_default=sa.text("'queued'")),
        sa.Column('retries', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('artifact_key', sa.String()),
        sa.Column('rq_job_id', sa.String()),
        sa.Column('error', sa.Text()),
        sa.Column('trace_id', sa.String()),
        sa.UniqueConstraint('job_type', 'input_hash', name='uq_jobs_type_input_hash')
    )

def downgrade():
    # Drop table first; if nothing else uses the enum, drop the type
    op.drop_table('jobs')
    op.execute("DROP TYPE IF EXISTS jobstatus;")
