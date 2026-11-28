"""Stored desired revision identity, not evidence of engine state."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import CharField, ForeignKeyField


class XrayDesiredRevisionModel(PersistenceEntity):
    node_id: int = ForeignKeyField("tbl_nodes.id", ondelete="RESTRICT")
    instance_id: str = CharField(63)
    revision_id: int = ForeignKeyField(
        "tbl_xray_revisions.id", ondelete="RESTRICT"
    )
