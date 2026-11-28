"""Record an immutable desired Xray revision per registered instance.

Revision ID: 0064
Revises: 0063
"""

import sqlalchemy as sa
from alembic import op

revision = "0064"
down_revision = "0063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_xray_desired_revisions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "node_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("instance_id", sa.String(63), nullable=False),
        sa.Column(
            "revision_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_xray_revisions.id", ondelete="RESTRICT"),
            nullable=False,
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
        sa.UniqueConstraint(
            "node_id", "instance_id", name="uq_xray_desired_revision_target"
        ),
    )


def downgrade() -> None:
    op.execute(
        "LOCK TABLE tbl_xray_desired_revisions IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM tbl_xray_desired_revisions) THEN
                RAISE EXCEPTION 'Cannot discard Xray desired assignments';
            END IF;
        END
        $$;
        """)
    op.drop_table("tbl_xray_desired_revisions")
