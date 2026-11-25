"""Store unique automatic transfer instructions on payments.

Revision ID: 0027
Revises: 0026
"""

import sqlalchemy as sa
from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tbl_payments", "receipt_id", nullable=True)
    op.add_column(
        "tbl_payments", sa.Column("transfer_amount", sa.BigInteger())
    )
    op.add_column("tbl_payments", sa.Column("confirmation_code", sa.String(5)))
    op.create_unique_constraint(
        "uq_tbl_payments_transfer_amount", "tbl_payments", ["transfer_amount"]
    )


def downgrade() -> None:
    op.alter_column("tbl_payments", "receipt_id", nullable=False)
    op.drop_constraint(
        "uq_tbl_payments_transfer_amount", "tbl_payments", type_="unique"
    )
    op.drop_column("tbl_payments", "confirmation_code")
    op.drop_column("tbl_payments", "transfer_amount")
