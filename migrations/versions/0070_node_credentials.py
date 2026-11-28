"""Store encrypted Node credentials with the registry.

Revision ID: 0070
Revises: 0069
"""

import os
from ipaddress import ip_address
from pathlib import Path

import sqlalchemy as sa
import yaml
from alembic import op
from cryptography.x509 import load_pem_x509_certificates
from papilio.core.config import get_settings
from papilio.security.crypto import encrypt

revision = "0070"
down_revision = "0069"
branch_labels = None
depends_on = None


def _canonical_address(address: str) -> str:
    try:
        return str(ip_address(address))
    except ValueError:
        return address.removesuffix(".").lower()


def _import_legacy_targets(path: str) -> None:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        legacy = data["node_host"]["targets"]
    except (OSError, UnicodeError, yaml.YAMLError, KeyError, TypeError):
        raise RuntimeError("Cannot read the legacy Node targets") from None
    if not isinstance(legacy, dict):
        raise RuntimeError("Legacy Node targets must be a mapping")

    rows: dict[int, tuple[str, int, str, str | None]] = {}
    for id, target in legacy.items():
        if isinstance(id, str) and id.isascii() and id.isdecimal():
            id = int(id)
        if type(id) is not int or id <= 0 or not isinstance(target, dict):
            raise RuntimeError("Invalid legacy Node target")
        address = target.get("address")
        port = target.get("port")
        api_key = target.get("api_key")
        ca_pem = target.get("ca_pem")
        if (
            not isinstance(address, str)
            or type(port) is not int
            or not isinstance(api_key, str)
            or not api_key
            or any(not 33 <= ord(char) <= 126 for char in api_key)
        ):
            raise RuntimeError("Invalid legacy Node target")
        if ca_pem is not None:
            try:
                if (
                    not isinstance(ca_pem, str)
                    or len(ca_pem) > 65536
                    or "PRIVATE KEY-----" in ca_pem
                    or not load_pem_x509_certificates(ca_pem.encode("ascii"))
                ):
                    raise ValueError
            except (UnicodeError, ValueError):
                raise RuntimeError("Invalid legacy Node CA bundle") from None
        if id in rows:
            raise RuntimeError("Duplicate legacy Node target")
        rows[id] = (_canonical_address(address), port, api_key, ca_pem)

    if rows:
        crypto = get_settings().crypto
        if crypto is None or crypto.encryption_key.strip() in {
            "",
            "replace-with-private-encryption-key",
        }:
            raise RuntimeError(
                "Node credential import requires the deployment encryption key"
            )
        table = sa.table(
            "tbl_nodes",
            sa.column("id", sa.BigInteger),
            sa.column("address", sa.String),
            sa.column("port", sa.Integer),
            sa.column("api_key_ciphertext", sa.Text),
            sa.column("ca_pem", sa.Text),
        )
        connection = op.get_bind()
        current = connection.execute(
            sa.select(table.c.id, table.c.address, table.c.port)
            .where(table.c.id.in_(rows))
            .order_by(table.c.id)
            .with_for_update()
        )
        matched = {id: (address, port) for id, address, port in current}
        if any(
            matched.get(id) != (address, port)
            for id, (address, port, _, _) in rows.items()
        ):
            raise RuntimeError("Legacy Node targets do not match the registry")
        stmt = table.update().where(table.c.id == sa.bindparam("node_id"))
        connection.execute(
            stmt,
            [
                {
                    "node_id": id,
                    "api_key_ciphertext": encrypt(
                        api_key, crypto.encryption_key
                    ),
                    "ca_pem": ca_pem,
                }
                for id, (_, _, api_key, ca_pem) in rows.items()
            ],
        )


def upgrade() -> None:
    op.add_column("tbl_nodes", sa.Column("api_key_ciphertext", sa.Text()))
    op.add_column("tbl_nodes", sa.Column("ca_pem", sa.Text()))
    op.add_column(
        "tbl_nodes",
        sa.Column(
            "connection_revision",
            sa.BigInteger(),
            server_default="1",
            nullable=False,
        ),
    )
    if path := os.environ.get("PAPILIOVPN_LEGACY_NODE_CONFIG"):
        _import_legacy_targets(path)


def downgrade() -> None:
    op.drop_column("tbl_nodes", "connection_revision")
    op.drop_column("tbl_nodes", "ca_pem")
    op.drop_column("tbl_nodes", "api_key_ciphertext")
