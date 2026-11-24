"""Store OCR attempts and the last extraction outcome on each receipt.

Revision ID: 0024
Revises: 0023
"""

import sqlalchemy as sa
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_receipts", sa.Column("extraction_status", sa.String(12))
    )
    op.create_table(
        "tbl_ocr_requests",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "receipt_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("error_code", sa.String(55)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_tbl_ocr_requests_receipt_id", "tbl_ocr_requests", ["receipt_id"]
    )


def downgrade() -> None:
    op.drop_table("tbl_ocr_requests")
    op.drop_column("tbl_receipts", "extraction_status")
