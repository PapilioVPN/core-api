"""Use native PostgreSQL operations for card transfer settings."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import func
from sqlmodel import col

from ....domain.enums.records import SettingsKey
from ....domain.models.records import TransferSettingsModel
from ..tables import CardTransferSettingsTable


class TransferSettingsRepository(
    PGPersistenceRepository[TransferSettingsModel]
):
    table = CardTransferSettingsTable

    async def find_by_key(
        self, key: SettingsKey
    ) -> TransferSettingsModel | None:
        """Read settings by their exact key.

        Args:
            key: Stored settings key.

        Returns:
            Matching settings, or None if they have never been saved.
        """
        settings = await self.get_one(col(self.table.key) == key)
        return settings

    async def save(self, data: TransferSettingsModel) -> TransferSettingsModel:
        """Upsert a policy atomically by its key.

        Args:
            data: Settings key and supplied fields. Omitted fields use model
                defaults on insert and stay unchanged on conflict.

        Returns:
            The saved row, retaining its identity on update.
        """
        columns = CardTransferSettingsTable.__table__.c
        fields = (columns.auto_confirm, columns.digits, columns.window_minutes)
        settings = await self.upsert(
            data,
            conflict_columns=[columns.key],
            update_columns=[
                field for field in fields if field.key in data.model_fields_set
            ],
            changes={columns.updated_at: func.current_timestamp()},
        )
        return settings
