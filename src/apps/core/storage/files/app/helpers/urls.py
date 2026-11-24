"""Construct stable file URLs from an explicitly configured public root."""

from urllib.parse import quote

from papilio.errors.exceptions import ValidationException
from pydantic import HttpUrl


def build_file_url(public_base_url: HttpUrl | None, key: str) -> str:
    """Append a storage-relative key to its public bucket/directory root.

    Args:
        public_base_url: Explicit public root, independent of SDK endpoints.
        key: Relative object key; never an absolute local filesystem path.

    Returns:
        Stable URL, preserving the configured root's path prefix.

    Raises:
        ValidationException: No public root is configured, or it contains
            credentials, a query or a fragment instead of a directory URL.
    """
    if (
        public_base_url is None
        or public_base_url.username
        or public_base_url.password
        or public_base_url.query
        or public_base_url.fragment
    ):
        raise ValidationException(
            message="Configure a public file base URL without credentials, "
            "query or fragment",
            message_code="file_public_url_invalid",
            loc=["public_base_url"],
        )
    url = f"{str(public_base_url).rstrip('/')}/{quote(key, safe='/')}"
    return url
