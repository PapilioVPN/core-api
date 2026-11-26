"""Store the latest connection observation for each managed node.

Revision ID: 0045
Revises: 0044
"""

import sqlalchemy as sa
from alembic import op

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_nodes",
        sa.Column(
            "connection_status",
            sa.String(12),
            server_default=sa.text("'unchecked'"),
            nullable=False,
        ),
    )
    op.add_column(
        "tbl_nodes",
        sa.Column("probe_started_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "tbl_nodes",
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "tbl_nodes",
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_nodes_probe_due",
        "tbl_nodes",
        [sa.text("probe_started_at NULLS FIRST"), "id"],
        postgresql_where=sa.text("is_enabled"),
    )


def downgrade() -> None:
    op.drop_index("ix_nodes_probe_due", table_name="tbl_nodes")
    op.drop_column("tbl_nodes", "last_seen_at")
    op.drop_column("tbl_nodes", "last_checked_at")
    op.drop_column("tbl_nodes", "probe_started_at")
    op.drop_column("tbl_nodes", "connection_status")
