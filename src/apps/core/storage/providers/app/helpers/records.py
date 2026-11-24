"""Validate stored connection JSON at its application trust boundary."""

from papilio.errors.exceptions import ValidationException
from pydantic import JsonValue, ValidationError

from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.results.records import (
    StorageProviderConnection,
)


def prepare_connection(
    provider_id: int, config: dict[str, JsonValue] | None
) -> StorageProviderConnection:
    """Validate stored JSON once without exposing credentials in errors.

    Args:
        provider_id: Identity returned by the configuration repository.
        config: Stored JSON, including absent or empty configuration.

    Returns:
        Materialized identity and usable typed S3 input without live resources.

    Raises:
        ValidationException: Stored settings are absent, empty or invalid.
            The error contains no credential-bearing validation details.
    """
    try:
        data = S3Config.model_validate(config)
    except ValidationError:
        raise ValidationException(
            message="Storage provider configuration is not ready for use",
            message_code="storage_provider_configuration_invalid",
            loc=["config"],
        ) from None
    connection = StorageProviderConnection(provider_id, data)
    return connection
