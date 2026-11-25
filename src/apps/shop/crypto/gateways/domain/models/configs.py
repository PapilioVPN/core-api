"""One encrypted JSON configuration per gateway account."""

from papilio.infra.db.dialects.postgresql import JSONBField
from papilio.infra.db.schema.entity import BaseEntity
from papilio.infra.db.schema.fields import ForeignKeyField
from pydantic import JsonValue


class GatewayConfigModel(BaseEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_crypto_gateways.id", ondelete="CASCADE", primary_key=True
    )
    config: dict[str, JsonValue] = JSONBField()
