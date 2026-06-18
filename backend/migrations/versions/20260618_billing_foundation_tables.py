"""create billing foundation tables

Revision ID: 20260618_billing_foundation
Revises: 20260618_billing_attempts
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260618_billing_foundation"
down_revision = "20260618_billing_attempts"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    if not _has_table("billing_subscriptions"):
        op.create_table(
            "billing_subscriptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=40), nullable=False),
            sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
            sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
            sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
            sa.Column("plan_code", sa.String(length=80), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_billing_subscriptions_id"),
            "billing_subscriptions",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_subscriptions_user_id"),
            "billing_subscriptions",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_subscriptions_provider"),
            "billing_subscriptions",
            ["provider"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_subscriptions_status"),
            "billing_subscriptions",
            ["status"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_subscriptions_current_period_end"),
            "billing_subscriptions",
            ["current_period_end"],
            unique=False,
        )

    if not _has_table("billing_events"):
        op.create_table(
            "billing_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=40), nullable=False),
            sa.Column("provider_event_id", sa.String(length=255), nullable=False),
            sa.Column("event_type", sa.String(length=255), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("payload_json", sa.JSON(), nullable=True),
            sa.Column("processing_status", sa.String(length=40), nullable=False),
            sa.Column("error_message", sa.String(length=1000), nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "provider",
                "provider_event_id",
                name="uq_billing_events_provider_event",
            ),
        )
        op.create_index(
            op.f("ix_billing_events_id"),
            "billing_events",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_events_provider"),
            "billing_events",
            ["provider"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_events_event_type"),
            "billing_events",
            ["event_type"],
            unique=False,
        )
        op.create_index(
            op.f("ix_billing_events_user_id"),
            "billing_events",
            ["user_id"],
            unique=False,
        )

    if not _has_table("manual_billing_overrides"):
        op.create_table(
            "manual_billing_overrides",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("plan_code", sa.String(length=80), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("reason", sa.String(length=1000), nullable=True),
            sa.Column("granted_by_admin_email", sa.String(length=320), nullable=True),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_manual_billing_overrides_id"),
            "manual_billing_overrides",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_manual_billing_overrides_user_id"),
            "manual_billing_overrides",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_manual_billing_overrides_status"),
            "manual_billing_overrides",
            ["status"],
            unique=False,
        )
        op.create_index(
            op.f("ix_manual_billing_overrides_ends_at"),
            "manual_billing_overrides",
            ["ends_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("manual_billing_overrides"):
        op.drop_table("manual_billing_overrides")

    if inspector.has_table("billing_events"):
        op.drop_table("billing_events")

    if inspector.has_table("billing_subscriptions"):
        op.drop_table("billing_subscriptions")
