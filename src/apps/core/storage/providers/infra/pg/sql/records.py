"""Narrow connection/configuration selections without database I/O."""

from pydantic import JsonValue
from sqlalchemy import Nullable, Select, select
from sqlmodel import col

from src.apps.core.storage.providers.infra.pg.tables import (
    StorageProviderConfigTable,
    StorageProviderTable,
)


class StorageProviderReadSQL:
    @staticmethod
    def select_active_configuration() -> Select[
        tuple[int, dict[str, JsonValue] | None]
    ]:
        """Select only the active connection ID and its stored JSON object.

        Args:
            None.

        Returns:
            An unexecuted left join preserving missing configurations as None
            and empty stored objects as {}. No descriptive fields are selected.
        """
        stmt = (
            select(
                col(StorageProviderTable.id),
                Nullable(col(StorageProviderConfigTable.config)),
            )
            .outerjoin(
                StorageProviderConfigTable,
                col(StorageProviderConfigTable.provider_id)
                == col(StorageProviderTable.id),
            )
            .where(col(StorageProviderTable.is_active).is_(True))
        )
        return stmt
