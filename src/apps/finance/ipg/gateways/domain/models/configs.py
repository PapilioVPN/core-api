"""Stored, encrypted provider configuration keyed by provider kind."""

from papilio.infra.db.dialects.postgresql import JSONBField
from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import EnumField
from pydantic import JsonValue

from ..enums.records import GatewayKind


class ConfigModel(PersistenceEntity):
    key: GatewayKind = EnumField(GatewayKind, length=32, unique=True)
    config: dict[str, JsonValue] = JSONBField()
