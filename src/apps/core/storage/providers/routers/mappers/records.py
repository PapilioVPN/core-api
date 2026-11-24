"""Whitelist public configuration fields without exposing credentials."""

from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
)
from src.apps.core.storage.providers.routers.schemas.configs import (
    S3ConfigOutput,
    StorageProviderConfigOutput,
)


class StorageProviderConfigMapper:
    @staticmethod
    def to_output(
        record: StorageProviderConfigModel,
    ) -> StorageProviderConfigOutput:
        """Map stored settings to the explicit public connection schema.

        Args:
            record: Materialized internal configuration, including {}.

        Returns:
            Public fields and nonempty-credential flags. Empty settings retain
            null fields and false flags without fabricating SDK defaults.
        """
        config = record.config
        public = S3ConfigOutput.from_dict(
            {
                "bucket": config.get("bucket"),
                "endpoint_url": config.get("endpoint_url"),
                "public_base_url": config.get("public_base_url"),
                "region_name": config.get("region_name"),
                "addressing_style": config.get("addressing_style"),
                "has_aws_access_key_id": bool(config.get("aws_access_key_id")),
                "has_aws_secret_access_key": bool(
                    config.get("aws_secret_access_key")
                ),
                "has_aws_session_token": bool(config.get("aws_session_token")),
            }
        )
        output = StorageProviderConfigOutput(
            provider_id=record.provider_id, is_empty=not config, config=public
        )
        return output
