"""Connection fields needed without descriptive provider metadata."""

from dataclasses import dataclass, field

from pydantic import JsonValue

from src.apps.core.storage.providers.domain.dtos.configs import S3Config


@dataclass(frozen=True, slots=True)
class StorageProviderConfigSnapshot:
    provider_id: int
    config: dict[str, JsonValue] | None = field(repr=False)


@dataclass(frozen=True, slots=True)
class StorageProviderConnection:
    """Validated connection for internal file-transfer consumers."""

    provider_id: int
    config: S3Config = field(repr=False)
