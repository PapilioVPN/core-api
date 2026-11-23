"""Persist bank references, card prefixes and receiving cards.

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_banks",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("title", sa.String(length=55), nullable=False),
        sa.Column("icon_url", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_banks_priority", "tbl_banks", ["priority", "id"])

    op.create_table(
        "tbl_card_prefixes",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("bank_id", sa.BigInteger(), nullable=False),
        sa.Column("prefix", sa.String(length=8), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bank_id"], ["tbl_banks.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_tbl_card_prefixes_bank_id", "tbl_card_prefixes", ["bank_id"]
    )

    op.create_table(
        "tbl_payment_cards",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("bank_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "card_number", sa.String(length=16), nullable=False, unique=True
        ),
        sa.Column("holder_name", sa.String(length=55), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("allow_manual", sa.Boolean(), nullable=False),
        sa.Column("allow_auto", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bank_id"], ["tbl_banks.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_tbl_payment_cards_bank_id", "tbl_payment_cards", ["bank_id"]
    )


def downgrade() -> None:
    op.drop_table("tbl_payment_cards")
    op.drop_table("tbl_card_prefixes")
    op.drop_table("tbl_banks")
