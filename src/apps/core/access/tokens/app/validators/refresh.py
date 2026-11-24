"""One-time refresh consumption failure semantics."""

from papilio.errors.exceptions import UnAuthorizedException


def validate_refresh_consumption(inserted: bool) -> None:
    """Reject an identity whose consumption was already recorded.

    Args:
        inserted: Actual atomic PostgreSQL insertion outcome.

    Returns:
        None for the winner; an unauthorized error for a repeated credential.
    """
    if not inserted:
        raise UnAuthorizedException(
            message="Refresh token was already used",
            message_code="refresh_token_used",
        )
