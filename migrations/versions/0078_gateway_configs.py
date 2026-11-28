"""Move encrypted provider settings into their own keyed tables.

Revision ID: 0078
Revises: 0077
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0078"
down_revision = "0077"
branch_labels = None
depends_on = None

_TABLES = (
    ("tbl_card_gateways", "tbl_card_gateway_configs"),
    ("tbl_ipg_gateways", "tbl_ipg_configs"),
)


def upgrade() -> None:
    for gateway, config in _TABLES:
        op.create_table(
            config,
            sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
            sa.Column("key", sa.String(32), nullable=False),
            sa.Column("config", postgresql.JSONB(), nullable=False),
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
            sa.UniqueConstraint("key", name=op.f(f"uq_{config}_key")),
            sa.ForeignKeyConstraint(
                ["key"],
                [f"{gateway}.kind"],
                name=op.f(f"fk_{config}_key_{gateway}"),
            ),
        )
        op.execute(
            sa.text(
                f"INSERT INTO {config} (key, config, created_at, updated_at) "
                f"SELECT kind, config, created_at, updated_at FROM {gateway}"
            )
        )
        op.drop_column(gateway, "config")


def downgrade() -> None:
    for gateway, config in _TABLES:
        op.add_column(gateway, sa.Column("config", postgresql.JSONB()))
        op.execute(
            sa.text(
                f"UPDATE {gateway} AS g SET config = COALESCE("
                f"(SELECT c.config FROM {config} AS c WHERE c.key = g.kind), "
                "'{}'::jsonb)"
            )
        )
        op.alter_column(gateway, "config", nullable=False)
        op.drop_table(config)
