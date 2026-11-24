"""Independent file metadata referencing shared physical content."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    CharField,
    ForeignKeyField,
    TextField,
)


class FileModel(PersistenceEntity):
    content_id: int = ForeignKeyField(
        "tbl_file_contents.id", ondelete="RESTRICT", index=True
    )
    original_name: str = TextField()
    mime_type: str = CharField(255)
