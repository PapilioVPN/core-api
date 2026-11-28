"""Persist ordered Xray restart plans and their individual operations.

Revision ID: 0061
Revises: 0060
"""

import sqlalchemy as sa
from alembic import op

revision = "0061"
down_revision = "0060"
branch_labels = None
depends_on = None


def _timestamps() -> tuple[sa.Column, ...]:
    return tuple(
        sa.Column(
            name,
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        )
        for name in ("created_at", "updated_at")
    )


def upgrade() -> None:
    op.create_table(
        "tbl_xray_restart_rollouts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("request_key", sa.Uuid(), nullable=False),
        sa.Column(
            "revision_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_xray_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("config_sha256", sa.String(64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(14), nullable=False),
        sa.Column("reason", sa.String(24)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.UniqueConstraint(
            "request_key", name="uq_xray_restart_rollout_request"
        ),
    )
    op.create_table(
        "tbl_xray_restart_rollout_targets",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "rollout_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_xray_restart_rollouts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "node_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("instance_id", sa.String(63), nullable=False),
        sa.Column("address", sa.String(253), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column(
            "operation_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_xray_starts.id", ondelete="RESTRICT"),
        ),
        *_timestamps(),
        sa.UniqueConstraint(
            "rollout_id", "position", name="uq_xray_restart_rollout_position"
        ),
        sa.UniqueConstraint(
            "rollout_id",
            "node_id",
            "instance_id",
            name="uq_xray_restart_rollout_target",
        ),
        sa.UniqueConstraint(
            "operation_id", name="uq_xray_restart_rollout_operation"
        ),
    )


def downgrade() -> None:
    op.execute("LOCK TABLE tbl_xray_restart_rollouts IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM tbl_xray_restart_rollouts) THEN
                RAISE EXCEPTION 'Cannot discard Xray restart rollout history';
            END IF;
        END
        $$;
        """)
    op.drop_table("tbl_xray_restart_rollout_targets")
    op.drop_table("tbl_xray_restart_rollouts")
