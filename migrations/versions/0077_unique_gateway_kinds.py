"""Allow one account for each payment provider kind.

Revision ID: 0077
Revises: 0076
"""

from alembic import op

revision = "0077"
down_revision = "0076"
branch_labels = None
depends_on = None

_TABLES = ("tbl_card_gateways", "tbl_ipg_gateways")


def upgrade() -> None:
    for table in _TABLES:
        op.create_unique_constraint(op.f(f"uq_{table}_kind"), table, ["kind"])


def downgrade() -> None:
    for table in _TABLES:
        op.drop_constraint(op.f(f"uq_{table}_kind"), table, type_="unique")
