"""Persist shop catalogs and their reusable sale terms.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_catalogs",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=55), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "published",
                "paused",
                name="catalogstatus",
                native_enum=False,
                length=12,
            ),
            nullable=False,
        ),
        sa.Column("volume_id", sa.BigInteger(), nullable=True),
        sa.Column("duration_id", sa.BigInteger(), nullable=True),
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
            ["service_id"], ["tbl_services.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["volume_id"], ["tbl_volumes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["duration_id"], ["tbl_durations.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_catalogs_service",
        "tbl_catalogs",
        ["service_id", "status", "priority", "id"],
    )


def downgrade() -> None:
    op.drop_table("tbl_catalogs")
