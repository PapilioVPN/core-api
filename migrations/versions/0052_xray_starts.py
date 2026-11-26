"""Record configured Xray start operations.

Revision ID: 0052
Revises: 0050
"""

import sqlalchemy as sa
from alembic import op

revision = "0052"
down_revision = "0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_xray_starts",
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
        sa.Column("request_key", sa.Uuid(), nullable=False),
        sa.Column("address", sa.String(253), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("deadline_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("reason", sa.String(24)),
        sa.Column("applied_config_sha256", sa.String(64)),
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
            name="uq_xray_start_request",
        ),
    )
    op.create_index(
        "uq_xray_start_active",
        "tbl_xray_starts",
        ["node_id", "instance_id"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_table("tbl_xray_starts")
