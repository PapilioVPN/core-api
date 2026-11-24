"""Validate the recorded S3 location without selecting another destination."""

from papilio.errors.exceptions import ValidationException
from pydantic import HttpUrl, ValidationError

from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.providers.domain.dtos.configs import S3Config


class FileDownloadValidation:
    @staticmethod
    def s3_provider_id(provider_id: int | None) -> int:
        """Require the original provider identity for S3 content.

        Args:
            provider_id: Recorded connection ID, never the active provider.
        Returns:
            Non-null original identity, including an inactive connection.
        Raises:
            ValidationException: The content record has no provider identity.
        """
        if provider_id is None:
            raise ValidationException(
                message="Stored S3 content has no provider identity",
                message_code="file_content_location_invalid",
                loc=["provider_id"],
            )
        return provider_id

    @staticmethod
    def s3_configuration(
        content: FileContentModel, access: S3Config
    ) -> S3Config:
        """Validate original location fields with current provider credentials.

        Args:
            content: Original bucket, endpoint and region saved at publication.
            access: Validated current credentials and native addressing style.
        Returns:
            A distinct typed connection to the recorded location. Optional
            endpoint/region remain None when originally absent; current upload
            destinations never replace them. Neither input is modified.
        Raises:
            ValidationException: The recorded location is incomplete/invalid;
                credential-bearing validation details are never exposed.
        """
        if content.bucket is None:
            raise ValidationException(
                message="Stored S3 content has no bucket",
                message_code="file_content_location_invalid",
                loc=["bucket"],
            )
        try:
            config = S3Config(
                bucket=content.bucket,
                endpoint_url=(
                    HttpUrl(content.endpoint_url)
                    if content.endpoint_url is not None
                    else None
                ),
                region_name=content.region_name,
                aws_access_key_id=access.aws_access_key_id,
                aws_secret_access_key=access.aws_secret_access_key,
                aws_session_token=access.aws_session_token,
                addressing_style=access.addressing_style,
            )
        except ValidationError:
            raise ValidationException(
                message="Stored S3 content location is invalid",
                message_code="file_content_location_invalid",
                loc=["content"],
            ) from None
        return config
