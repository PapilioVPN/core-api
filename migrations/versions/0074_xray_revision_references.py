"""Index assignment and operation references to saved Xray revisions.

Revision ID: 0074
Revises: 0073
"""

from alembic import op

revision = "0074"
down_revision = "0073"
branch_labels = None
depends_on = None

_TABLES = (
    "tbl_xray_desired_revisions",
    "tbl_xray_restart_rollouts",
    "tbl_xray_starts",
)


def upgrade() -> None:
    for table in _TABLES:
        op.create_index(
            op.f(f"ix_{table}_revision_id"), table, ["revision_id"]
        )


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_index(op.f(f"ix_{table}_revision_id"), table_name=table)
