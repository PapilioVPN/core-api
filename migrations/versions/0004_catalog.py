"""Persist catalog categories, attributes and their assignments.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tbl_attributes",
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
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("key", sa.String(length=35), nullable=False),
        sa.Column("label", sa.String(length=55), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "str",
                "int",
                "bool",
                name="attributetype",
                native_enum=False,
                length=10,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "param_key",
            sa.Enum(
                "duration_days",
                "quota_bytes",
                name="paramkey",
                native_enum=False,
                length=24,
            ),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
        sa.UniqueConstraint("param_key"),
    )
    op.create_table(
        "tbl_categories",
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
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=55), nullable=False),
        sa.Column("title", sa.String(length=55), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "tbl_category_attributes",
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("attribute_id", sa.BigInteger(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_filterable", sa.Boolean(), nullable=False),
        sa.Column("is_variant_axis", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attribute_id"], ["tbl_attributes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["tbl_categories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("category_id", "attribute_id"),
    )
    op.create_index(
        op.f("ix_tbl_category_attributes_attribute_id"),
        "tbl_category_attributes",
        ["attribute_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_tbl_category_attributes_attribute_id"),
        table_name="tbl_category_attributes",
    )
    op.drop_table("tbl_category_attributes")
    op.drop_table("tbl_categories")
    op.drop_table("tbl_attributes")
