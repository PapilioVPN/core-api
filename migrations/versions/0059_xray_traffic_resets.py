"""Store durable technical traffic resets and Node evidence.

Revision ID: 0059
Revises: 0058
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_xray_traffic_resets",
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
        sa.Column("scope", sa.String(12), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("name", sa.String(4096)),
        sa.Column("direction", sa.String(12)),
        sa.Column("max_counters", sa.Integer()),
        sa.Column("counters", JSON()),
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
            name="uq_xray_reset_request",
        ),
    )
    op.create_index(
        "uq_xray_reset_active",
        "tbl_xray_traffic_resets",
        ["node_id", "instance_id"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.execute("LOCK TABLE tbl_xray_traffic_resets IN ACCESS EXCLUSIVE MODE")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM tbl_xray_traffic_resets) THEN
                RAISE EXCEPTION
                    'Cannot discard Xray traffic reset history';
            END IF;
        END
        $$;
        """
    )
    op.drop_table("tbl_xray_traffic_resets")
