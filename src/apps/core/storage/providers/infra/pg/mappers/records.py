"""Materialize narrow connection fields for application consumers."""

from pydantic import JsonValue

from src.apps.core.storage.providers.domain.results.records import (
    StorageProviderConfigSnapshot,
)


class StorageProviderMapper:
    @staticmethod
    def to_config_snapshot(
        row: tuple[int, dict[str, JsonValue] | None],
    ) -> StorageProviderConfigSnapshot:
        """Materialize the selected connection identity and configuration.

        Args:
            row: Provider ID and optional JSON object from the left join.

        Returns:
            A snapshot independent of ORM relationships or open resources,
            preserving missing and empty configurations distinctly.
        """
        snapshot = StorageProviderConfigSnapshot(row[0], row[1])
        return snapshot
