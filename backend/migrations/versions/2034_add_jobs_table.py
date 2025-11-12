# ruff: noqa: I001
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2034"
down_revision = "2033"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    statuses = ("queued", "running", "succeeded", "failed")

    if dialect == "postgresql":
        jobstatus = postgresql.ENUM(*statuses, name="jobstatus", create_type=True)
        jobstatus.create(bind=bind, checkfirst=True)
        status_col = sa.Column("status", jobstatus, nullable=False, server_default="queued")
        now = sa.text("now()")
    else:
        # SQLite (and others) -> store as TEXT with Enum emulation
        jobstatus = sa.Enum(*statuses, name="jobstatus", native_enum=False)
        status_col = sa.Column(
            "status", jobstatus, nullable=False, server_default=sa.text("'queued'")
        )
        now = sa.text("CURRENT_TIMESTAMP")

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        status_col,
        sa.Column("retries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=now),
        sa.Column("started_at", sa.DateTime),
        sa.Column("ended_at", sa.DateTime),
        sa.Column("artifact_key", sa.String(255)),
        sa.Column("rq_job_id", sa.String(64)),
        sa.Column("error", sa.Text),
        sa.Column("trace_id", sa.String(64)),
        sa.UniqueConstraint("job_type", "input_hash", name="uq_jobs_job_type_input_hash"),
    )


def downgrade():
    op.drop_table("jobs")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        postgresql.ENUM(name="jobstatus").drop(bind=bind, checkfirst=True)
