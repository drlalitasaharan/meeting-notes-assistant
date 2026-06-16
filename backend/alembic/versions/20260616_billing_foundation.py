"""add billing foundation

Revision ID: 20260616_billing_foundation
Revises: 2033
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260616_billing_foundation"
down_revision = "2033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("plan_code", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_billing_subscriptions_user_id", "billing_subscriptions", ["user_id"])
    op.create_index("ix_billing_subscriptions_provider", "billing_subscriptions", ["provider"])
    op.create_index("ix_billing_subscriptions_status", "billing_subscriptions", ["status"])
    op.create_index(
        "ix_billing_subscriptions_current_period_end",
        "billing_subscriptions",
        ["current_period_end"],
    )

    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("processing_status", sa.String(length=40), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "provider", "provider_event_id", name="uq_billing_events_provider_event"
        ),
    )
    op.create_index("ix_billing_events_provider", "billing_events", ["provider"])
    op.create_index("ix_billing_events_event_type", "billing_events", ["event_type"])
    op.create_index("ix_billing_events_user_id", "billing_events", ["user_id"])

    op.create_table(
        "manual_billing_overrides",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_code", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column("granted_by_admin_email", sa.String(length=320), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_manual_billing_overrides_user_id", "manual_billing_overrides", ["user_id"])
    op.create_index("ix_manual_billing_overrides_status", "manual_billing_overrides", ["status"])
    op.create_index("ix_manual_billing_overrides_ends_at", "manual_billing_overrides", ["ends_at"])


def downgrade() -> None:
    op.drop_index("ix_manual_billing_overrides_ends_at", table_name="manual_billing_overrides")
    op.drop_index("ix_manual_billing_overrides_status", table_name="manual_billing_overrides")
    op.drop_index("ix_manual_billing_overrides_user_id", table_name="manual_billing_overrides")
    op.drop_table("manual_billing_overrides")

    op.drop_index("ix_billing_events_user_id", table_name="billing_events")
    op.drop_index("ix_billing_events_event_type", table_name="billing_events")
    op.drop_index("ix_billing_events_provider", table_name="billing_events")
    op.drop_table("billing_events")

    op.drop_index("ix_billing_subscriptions_current_period_end", table_name="billing_subscriptions")
    op.drop_index("ix_billing_subscriptions_status", table_name="billing_subscriptions")
    op.drop_index("ix_billing_subscriptions_provider", table_name="billing_subscriptions")
    op.drop_index("ix_billing_subscriptions_user_id", table_name="billing_subscriptions")
    op.drop_table("billing_subscriptions")
