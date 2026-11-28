"""Store durable operator routing requests and delivery outcomes.

Revision ID: 0056
Revises: 0055
"""

import sqlalchemy as sa
from alembic import op

revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_xray_routing_operations",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(),
            primary_key=True,
        ),
        sa.Column(
            "node_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("instance_id", sa.String(63), nullable=False),
        sa.Column("address", sa.String(253), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("request_key", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("state", sa.String(14), nullable=False),
        sa.Column("reason", sa.String(24)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("deadline_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "node_id",
            "instance_id",
            "request_key",
            name="uq_xray_routing_request",
        ),
    )
    op.create_index(
        "uq_xray_routing_active",
        "tbl_xray_routing_operations",
        ["node_id", "instance_id"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.execute(
        "LOCK TABLE tbl_xray_routing_operations IN ACCESS EXCLUSIVE MODE"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM tbl_xray_routing_operations) THEN
                RAISE EXCEPTION
                    'Cannot discard Xray routing operation history';
            END IF;
        END
        $$;
        """
    )
    op.drop_table("tbl_xray_routing_operations")
