"""Store IPG bank references and indexed reconciliation timing.

Revision ID: 0081
Revises: 0080
"""

import sqlalchemy as sa
from alembic import op

revision = "0081"
down_revision = "0080"
branch_labels = None
depends_on = None

_TABLE = "tbl_ipg_payments"
_INDEX = "ix_ipg_payments_due"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("credential", sa.Text()))
    op.add_column(_TABLE, sa.Column("tracking_code", sa.String(128)))
    op.add_column(
        _TABLE, sa.Column("next_check_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        _TABLE, sa.Column("confirmed_at", sa.DateTime(timezone=True))
    )
    op.execute(
        sa.text(
            "UPDATE tbl_ipg_payments AS p "
            "SET credential = c.config ->> 'merchant_id', "
            "next_check_at = CURRENT_TIMESTAMP "
            "FROM tbl_ipg_gateways AS g JOIN tbl_ipg_configs AS c "
            "ON c.key = g.kind WHERE p.gateway_id = g.id "
            "AND p.status = 'ready'"
        )
    )
    op.create_index(
        _INDEX,
        _TABLE,
        ["next_check_at", "id"],
        postgresql_where=sa.text(
            "status = 'ready' AND next_check_at IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE tbl_ipg_payments SET status = 'ready' "
            "WHERE status = 'confirmed'"
        )
    )
    op.drop_index(_INDEX, table_name=_TABLE)
    op.drop_column(_TABLE, "confirmed_at")
    op.drop_column(_TABLE, "next_check_at")
    op.drop_column(_TABLE, "tracking_code")
    op.drop_column(_TABLE, "credential")
