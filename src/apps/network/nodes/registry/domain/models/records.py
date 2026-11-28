"""Stored operator-managed node identity and address."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    BoolField,
    CharField,
    EnumField,
    IntField,
    TimestampField,
)
from sqlalchemy import Text, text
from sqlmodel import Field

from src.apps.network.nodes.connections.domain.enums.connection import (
    NodeConnectionStatus,
)

from ..dtos.records import DEFAULT_TIMEOUT
from ..results.records import NodeEndpoint


class NodeModel(PersistenceEntity):
    name: str = CharField(55)
    address: str = CharField(253)
    port: int = IntField()
    default_timeout: int = IntField(
        default=DEFAULT_TIMEOUT, server_default=text(str(DEFAULT_TIMEOUT))
    )
    is_enabled: bool = BoolField(default=True)
    sort_order: int | None = BigIntField(default=None, nullable=True)
    connection_revision: int = BigIntField(default=1, server_default=text("1"))
    api_key_ciphertext: str | None = Field(
        nullable=True, default=None, repr=False, sa_type=Text
    )
    ca_pem: str | None = Field(
        nullable=True, default=None, repr=False, sa_type=Text
    )
    connection_status: NodeConnectionStatus = EnumField(
        NodeConnectionStatus,
        length=12,
        default=NodeConnectionStatus.UNCHECKED,
        server_default=text("'unchecked'"),
    )
    probe_started_at: datetime | None = TimestampField(
        nullable=True, default=None
    )
    last_checked_at: datetime | None = TimestampField(
        nullable=True, default=None
    )
    last_seen_at: datetime | None = TimestampField(nullable=True, default=None)

    def endpoint(self) -> NodeEndpoint:
        """Materialize the exact connection destination for a remote call."""
        return NodeEndpoint(
            self.id,
            self.address,
            self.port,
            self.is_enabled,
            self.connection_revision,
            self.api_key_ciphertext,
            self.ca_pem,
            self.default_timeout,
        )
