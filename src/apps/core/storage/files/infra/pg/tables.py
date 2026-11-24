"""Shared physical content with independently retained file references."""

from papilio.infra.db.table import BaseTable
from sqlmodel import Relationship

from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.domain.models.records import FileModel


class FileContentTable(FileContentModel, BaseTable, table=True):
    files: list["FileTable"] = Relationship(
        back_populates="content",
        sa_relationship_kwargs={"lazy": "raise", "passive_deletes": "all"},
    )


class FileTable(FileModel, BaseTable, table=True):
    content: FileContentTable = Relationship(
        back_populates="files", sa_relationship_kwargs={"lazy": "raise"}
    )
