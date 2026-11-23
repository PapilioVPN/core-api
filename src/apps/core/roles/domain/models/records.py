"""Native role and role-scope persistence declarations."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
    SmallIntField,
    TextField,
)


class RoleModel(PersistenceEntity):
    key: str = CharField(55, unique=True)
    title: str = CharField(55)
    description: str | None = TextField(nullable=True, default=None)
    is_active: bool = BoolField(default=True)


class RoleScopeModel(PersistenceEntity):
    role_id: int = ForeignKeyField("tbl_roles.id", ondelete="CASCADE")
    scope_id: int = ForeignKeyField("tbl_scopes.id", index=True)
    permissions: int = SmallIntField()
