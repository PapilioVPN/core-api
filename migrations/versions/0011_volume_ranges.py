"""Persist service-owned custom volume ranges.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ExcludeConstraint

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_volume_ranges",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("min_bytes", sa.BigInteger(), nullable=False),
        sa.Column("max_bytes", sa.BigInteger(), nullable=False),
        sa.Column("step_bytes", sa.BigInteger(), nullable=False),
        sa.Column("price_per_gib", sa.BigInteger(), nullable=False),
        sa.Column("min_days", sa.Integer(), nullable=True),
        sa.Column("max_days", sa.Integer(), nullable=True),
        sa.Column("step_days", sa.Integer(), nullable=True),
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
        ExcludeConstraint(
            (sa.text("numrange(service_id, service_id, '[]')"), "="),
            (sa.text("int8range(min_bytes, max_bytes, '[]')"), "&&"),
            name="excl_volume_ranges_overlap",
            using="gist",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"], ["tbl_services.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_volume_ranges_service",
        "tbl_volume_ranges",
        ["service_id", "min_bytes"],
    )


def downgrade() -> None:
    op.drop_table("tbl_volume_ranges")
