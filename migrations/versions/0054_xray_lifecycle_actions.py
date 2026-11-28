"""Track control actions and confirmed Stops alongside Xray starts.

Revision ID: 0054
Revises: 0053
"""

import sqlalchemy as sa
from alembic import op

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_xray_starts",
        sa.Column(
            "action", sa.String(12), server_default="start", nullable=False
        ),
    )
    op.add_column(
        "tbl_xray_starts", sa.Column("stopped_at", sa.DateTime(timezone=True))
    )


def downgrade() -> None:
    op.execute("LOCK TABLE tbl_xray_starts IN ACCESS EXCLUSIVE MODE")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM tbl_xray_starts WHERE action <> 'start'
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade while Xray control operations exist';
            END IF;
        END
        $$;
        """
    )
    op.drop_column("tbl_xray_starts", "stopped_at")
    op.drop_column("tbl_xray_starts", "action")
