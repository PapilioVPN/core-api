"""Create the shared storage tables.

Revision ID: 0018
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0018"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_storage_providers",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("key", sa.String(55), nullable=False),
        sa.Column("title", sa.String(55), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("key"),
    )
    op.create_index(
        "uq_storage_providers_active",
        "tbl_storage_providers",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.create_table(
        "tbl_storage_provider_configs",
        sa.Column(
            "provider_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_storage_providers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("config", postgresql.JSONB(), nullable=False),
    )

    op.create_table(
        "tbl_storage_configs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("backend", sa.String(5), nullable=False),
    )
    op.create_index(
        "uq_storage_configs_singleton",
        "tbl_storage_configs",
        [sa.text("(true)")],
        unique=True,
    )

    op.create_table(
        "tbl_file_contents",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("backend", sa.String(5), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("provider_id", sa.BigInteger(), nullable=True),
        sa.Column("bucket", sa.Text(), nullable=True),
        sa.Column("endpoint_url", sa.Text(), nullable=True),
        sa.Column("region_name", sa.Text(), nullable=True),
        sa.UniqueConstraint("sha256"),
        sa.ForeignKeyConstraint(
            ["provider_id"], ["tbl_storage_providers.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_tbl_file_contents_provider_id",
        "tbl_file_contents",
        ["provider_id"],
    )
    op.create_table(
        "tbl_files",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_id"], ["tbl_file_contents.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_tbl_files_content_id", "tbl_files", ["content_id"])


def downgrade() -> None:
    op.drop_table("tbl_files")
    op.drop_table("tbl_file_contents")
    op.drop_table("tbl_storage_configs")
    op.drop_table("tbl_storage_provider_configs")
    op.drop_table("tbl_storage_providers")
