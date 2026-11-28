"""Store the default RPC timeout on the node record.

Revision ID: 0072
Revises: 0071
"""

import sqlalchemy as sa
from alembic import op

revision = "0072"
down_revision = "0071"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_nodes",
        sa.Column(
            "default_timeout",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("10"),
        ),
    )


def downgrade() -> None:
    op.drop_column("tbl_nodes", "default_timeout")
