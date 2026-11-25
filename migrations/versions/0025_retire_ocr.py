"""Retire receipt OCR and preserve historical extraction results.

Revision ID: 0025
Revises: 0024
"""

from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("tbl_ocr_requests", "tbl_ocr_requests_legacy")
    op.alter_column(
        "tbl_receipts",
        "extraction_status",
        new_column_name="legacy_extraction_status",
    )


def downgrade() -> None:
    op.alter_column(
        "tbl_receipts",
        "legacy_extraction_status",
        new_column_name="extraction_status",
    )
    op.rename_table("tbl_ocr_requests_legacy", "tbl_ocr_requests")
