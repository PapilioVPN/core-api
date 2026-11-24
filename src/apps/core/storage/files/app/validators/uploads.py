"""Publication checks using already-read upload facts."""

from papilio.errors.exceptions import ConflictException, ValidationException

from src.apps.core.storage.files.domain.models.contents import FileContentModel


class FileUploadValidation:
    @staticmethod
    def content_url(content: FileContentModel) -> str:
        """Require the original stored URL without reading configuration.

        Args:
            content: Already materialized content, including legacy records.

        Returns:
            Original stable URL, independent of the current upload backend.

        Raises:
            ValidationException: A legacy content record has no configured URL.
        """
        if content.url is None:
            raise ValidationException(
                message="Stored file content has no access URL",
                message_code="file_content_url_missing",
                loc=["url"],
            )
        return content.url

    @staticmethod
    def published_content(
        sha256: str, content: FileContentModel | None
    ) -> FileContentModel:
        """Require new publication when no committed content was found.

        Args:
            sha256: Staged digest identifying the unresolved collision.
            content: New physical metadata, or None without publication.
        Returns:
            Trusted new metadata, without examining or adopting existing bytes.
        Raises:
            ConflictException: No current content or new publication exists.
        """
        if content is None:
            raise ConflictException(
                message="Stored path has no registered content",
                message_code="unregistered_file_content",
                unique_dict={"sha256": sha256},
            )
        return content
