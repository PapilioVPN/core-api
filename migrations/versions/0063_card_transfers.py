"""Record inbound bank transfers independently of card payments.

Revision ID: 0063
Revises: 0062
"""

import sqlalchemy as sa
from alembic import op

revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_card_transfers",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "card_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_payment_cards.id", ondelete="RESTRICT"),
        ),
        sa.Column("transferred_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(8), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
    )
    op.create_index(
        "ix_tbl_card_transfers_amount", "tbl_card_transfers", ["amount"]
    )
    op.create_index(
        "ix_tbl_card_transfers_card_id", "tbl_card_transfers", ["card_id"]
    )


def downgrade() -> None:
    op.drop_table("tbl_card_transfers")
