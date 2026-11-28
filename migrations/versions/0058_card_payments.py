"""Create manual payments with destination cards and receipt addresses.

Revision ID: 0058
Revises: 0057
"""

import sqlalchemy as sa
from alembic import op

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_card_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "card_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_payment_cards.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("receipt_url", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("rejection_reason", sa.String(500)),
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
    op.create_index(
        "ix_tbl_card_payments_card_id", "tbl_card_payments", ["card_id"]
    )


def downgrade() -> None:
    op.drop_table("tbl_card_payments")
