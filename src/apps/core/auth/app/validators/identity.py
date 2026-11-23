"""Native account-ID adaptation after JWT protocol verification."""

from uuid import UUID

from papilio.core import resources
from papilio.errors.exceptions import UnAuthorizedException
from papilio.types.aliases import IdType
from pydantic import TypeAdapter, ValidationError

from src.apps.core.tokens.domain.models.tokens import VerifiedToken

USER_ID_ADAPTER: TypeAdapter[int] = TypeAdapter(IdType)


def session_unavailable() -> UnAuthorizedException:
    """Build the standard error for an unavailable session.

    Args:
        None.

    Returns:
        Authentication error shared by missing and closed sessions.
    """
    return UnAuthorizedException(
        message="Session is unavailable", message_code="session_unavailable"
    )


def require_session_id(verified: VerifiedToken) -> UUID:
    """Require a session-bound administrator credential.

    Args:
        verified: Already verified access or refresh token.

    Returns:
        The session UUID carried by the credential.

    Raises:
        UnAuthorizedException: The credential has no session UUID.
    """
    session_id = verified.identity.session_id
    if session_id is None:
        raise session_unavailable()
    return session_id


def parse_admin_subject(verified: VerifiedToken) -> int:
    """Read the native account identity after credential verification.

    Args:
        verified: Admin-audience metadata verified by the owning token service.

    Returns:
        Positive internal account ID; no role or scope claims are required.

    Raises:
        UnAuthorizedException: Subject does not satisfy the native ID contract.
    """
    try:
        user_id = USER_ID_ADAPTER.validate_python(verified.identity.subject)
    except ValidationError as exc:
        raise UnAuthorizedException(
            message="Invalid authentication token",
            message_code=resources.INVALID_TOKEN,
        ) from exc
    return user_id
