"""Account persistence, independent of employment and personnel records."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
)


class UserModel(PersistenceEntity):
    first_name: str = CharField(55)
    last_name: str = CharField(55)
    mobile: str = CharField(11, unique=True)
    email: str | None = CharField(100, nullable=True, default=None)
    role_id: int = ForeignKeyField(
        "tbl_roles.id", ondelete="RESTRICT", index=True
    )
    is_active: bool = BoolField(default=True)
    is_super_admin: bool = BoolField(default=False)
    hashed_password: str | None = CharField(100, nullable=True, default=None)
