"""Keep fixed volumes active and retain previously saved ranges.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("LOCK TABLE tbl_volumes IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        CREATE TABLE tbl_volume_ranges_legacy AS
        SELECT * FROM tbl_volumes WHERE mode = 'custom'
    """)
    op.execute("DELETE FROM tbl_volumes WHERE mode = 'custom'")
    op.drop_index("uq_volumes_terms", table_name="tbl_volumes")
    for column in ("mode", "min_bytes", "max_bytes", "step_bytes"):
        op.drop_column("tbl_volumes", column)
    op.alter_column("tbl_volumes", "size_bytes", nullable=False)
    op.create_index(
        "uq_volumes_terms",
        "tbl_volumes",
        ["size_bytes"],
        unique=True,
        postgresql_where=sa.text("is_canonical"),
    )


def downgrade() -> None:
    op.drop_index("uq_volumes_terms", table_name="tbl_volumes")
    op.add_column(
        "tbl_volumes",
        sa.Column(
            "mode", sa.String(8), server_default="fixed", nullable=False
        ),
    )
    op.alter_column("tbl_volumes", "mode", server_default=None)
    for column in ("min_bytes", "max_bytes", "step_bytes"):
        op.add_column("tbl_volumes", sa.Column(column, sa.BigInteger()))
    op.alter_column("tbl_volumes", "size_bytes", nullable=True)
    op.execute("""
        INSERT INTO tbl_volumes (
            id, mode, size_bytes, min_bytes, max_bytes, step_bytes, created_at,
            is_canonical
        )
        SELECT id, mode, size_bytes, min_bytes, max_bytes, step_bytes,
               created_at, is_canonical
        FROM tbl_volume_ranges_legacy
    """)
    op.drop_table("tbl_volume_ranges_legacy")
    op.create_index(
        "uq_volumes_terms",
        "tbl_volumes",
        ["mode", "size_bytes", "min_bytes", "max_bytes", "step_bytes"],
        unique=True,
        postgresql_nulls_not_distinct=True,
        postgresql_where=sa.text("is_canonical"),
    )
