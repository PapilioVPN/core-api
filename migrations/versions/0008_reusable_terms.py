"""Select canonical shop terms while preserving existing identities.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    terms = (
        (
            "tbl_volumes",
            "uq_volumes_terms",
            ["mode", "size_bytes", "min_bytes", "max_bytes", "step_bytes"],
        ),
        ("tbl_durations", "uq_durations_terms", ["days", "starts_on"]),
    )
    for table, index, columns in terms:
        op.add_column(
            table,
            sa.Column(
                "is_canonical",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            ),
        )
        by_terms = ", ".join(columns)
        op.execute(
            sa.text(f"""
            UPDATE {table} AS term
            SET is_canonical = false
            FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY {by_terms} ORDER BY id
                ) AS position
                FROM {table}
            ) AS ranked
            WHERE ranked.id = term.id AND ranked.position > 1
        """)
        )
        op.create_index(
            index,
            table,
            columns,
            unique=True,
            postgresql_where=sa.text("is_canonical"),
            postgresql_nulls_not_distinct=True
            if table == "tbl_volumes"
            else None,
        )


def downgrade() -> None:
    op.drop_index("uq_durations_terms", table_name="tbl_durations")
    op.drop_index("uq_volumes_terms", table_name="tbl_volumes")
    op.drop_column("tbl_durations", "is_canonical")
    op.drop_column("tbl_volumes", "is_canonical")
