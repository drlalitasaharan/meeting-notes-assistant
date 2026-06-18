"""add billing payment attempts

Revision ID: 20260618_billing_attempts
Revises: 9fc26ee281f2
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260618_billing_attempts"
down_revision = "9fc26ee281f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_payment_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("attempt_reference", sa.String(length=80), nullable=False),
        sa.Column("provider_order_id", sa.String(length=255), nullable=True),
        sa.Column("provider_capture_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("checkout_url", sa.String(length=2000), nullable=True),
        sa.Column("plan_code", sa.String(length=80), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "attempt_reference",
            name="uq_billing_payment_attempts_provider_reference",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_order_id",
            name="uq_billing_payment_attempts_provider_order",
        ),
    )
    op.create_index(
        op.f("ix_billing_payment_attempts_id"),
        "billing_payment_attempts",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_payment_attempts_user_id"),
        "billing_payment_attempts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_payment_attempts_provider"),
        "billing_payment_attempts",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_payment_attempts_attempt_reference"),
        "billing_payment_attempts",
        ["attempt_reference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_payment_attempts_provider_order_id"),
        "billing_payment_attempts",
        ["provider_order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_payment_attempts_status"),
        "billing_payment_attempts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_billing_payment_attempts_status"), table_name="billing_payment_attempts")
    op.drop_index(
        op.f("ix_billing_payment_attempts_provider_order_id"), table_name="billing_payment_attempts"
    )
    op.drop_index(
        op.f("ix_billing_payment_attempts_attempt_reference"), table_name="billing_payment_attempts"
    )
    op.drop_index(
        op.f("ix_billing_payment_attempts_provider"), table_name="billing_payment_attempts"
    )
    op.drop_index(
        op.f("ix_billing_payment_attempts_user_id"), table_name="billing_payment_attempts"
    )
    op.drop_index(op.f("ix_billing_payment_attempts_id"), table_name="billing_payment_attempts")
    op.drop_table("billing_payment_attempts")
