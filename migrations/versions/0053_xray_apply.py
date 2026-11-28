"""Link tracked Xray applications to their saved revision.

Revision ID: 0053
Revises: 0052
"""

import sqlalchemy as sa
from alembic import op

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tbl_xray_starts", sa.Column("revision_id", sa.BigInteger()))
    op.create_foreign_key(
        "fk_xray_starts_revision",
        "tbl_xray_starts",
        "tbl_xray_revisions",
        ["revision_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.execute("LOCK TABLE tbl_xray_starts IN ACCESS EXCLUSIVE MODE")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM tbl_xray_starts WHERE revision_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade while Xray revision operations exist';
            END IF;
        END
        $$;
        """
    )
    op.drop_constraint(
        "fk_xray_starts_revision", "tbl_xray_starts", type_="foreignkey"
    )
    op.drop_column("tbl_xray_starts", "revision_id")
