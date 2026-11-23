"""Native account-ID adaptation after JWT protocol verification."""

from papilio.core import resources
from papilio.errors.exceptions import UnAuthorizedException
from papilio.types.aliases import IdType
from pydantic import TypeAdapter, ValidationError

from src.apps.core.auth.domain.dtos.identity import AdminClaims
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.tokens.domain.models.tokens import VerifiedToken

USER_ID_ADAPTER: TypeAdapter[int] = TypeAdapter(IdType)


def parse_admin_identity(verified: VerifiedToken) -> AdminIdentity:
    """Adapt the verified subject and administrator claims to a typed identity.

    Args:
        verified: Token already checked for admin audience and access kind.

    Returns:
        Internal user/role IDs and the scope masks captured in the payload.

    Raises:
        UnAuthorizedException: The subject or owner claim shape is invalid.
    """
    user_id = parse_admin_subject(verified)
    try:
        claims = AdminClaims.model_validate(
            verified.identity.claims, strict=True
        )
    except ValidationError as exc:
        raise UnAuthorizedException(
            message="Invalid authentication token",
            message_code=resources.INVALID_TOKEN,
        ) from exc
    result = AdminIdentity(
        user_id=user_id, role_id=claims.role_id, scopes=claims.scopes
    )
    return result


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
