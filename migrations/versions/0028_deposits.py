"""Store bank reports and the payment matched to each report.

Revision ID: 0028
Revises: 0027
"""

import sqlalchemy as sa
from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_deposits",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column(
            "payment_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_payments.id", ondelete="RESTRICT"),
            unique=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index("ix_tbl_deposits_amount", "tbl_deposits", ["amount"])


def downgrade() -> None:
    op.drop_table("tbl_deposits")
