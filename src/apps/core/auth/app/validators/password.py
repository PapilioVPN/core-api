"""Pure eligibility checks for administrator password login."""

from papilio.errors.exceptions import UnAuthorizedException

from src.apps.core.roles.domain.results.records import RoleAccess
from src.apps.core.users.domain.models.records import UserModel
from src.apps.core.users.domain.results.records import UserAccess


def require_active_user[T: (UserModel, UserAccess)](user: T | None) -> T:
    """Require an existing active account before checking its password.

    Args:
        user: Authoritative account lookup result, or None.

    Returns:
        The unchanged active account.

    Raises:
        UnAuthorizedException: Account is missing or inactive.
    """
    if user is None or not user.is_active:
        raise UnAuthorizedException(
            message="Invalid credentials", message_code="invalid_credentials"
        )
    return user


def require_password_hash(password_hash: str | None) -> str:
    """Require a stored password verifier without inventing a fallback.

    Args:
        password_hash: Stored hash, or None for a passwordless account.

    Returns:
        The nonempty hash; its format is checked by the native verifier.

    Raises:
        UnAuthorizedException: No password hash is stored.
    """
    if not password_hash:
        raise UnAuthorizedException(
            message="Invalid credentials", message_code="invalid_credentials"
        )
    return password_hash


def validate_password_match(matches: bool) -> None:
    """Require a successful native password comparison.

    Args:
        matches: Native verifier outcome, including False for malformed hashes.

    Returns:
        None on a match.

    Raises:
        UnAuthorizedException: Password does not match the stored verifier.
    """
    if not matches:
        raise UnAuthorizedException(
            message="Invalid credentials", message_code="invalid_credentials"
        )


def require_active_role(
    role: RoleAccess | None, *, super_admin: bool = False
) -> RoleAccess:
    """Require an existing active role before issuing access claims.

    Args:
        role: Materialized assigned-role lookup result, or None.

    Returns:
        The unchanged role with its active scope masks.

    Raises:
        UnAuthorizedException: Assigned role is missing or inactive.
    """
    if role is None or (not role.is_active and not super_admin):
        raise UnAuthorizedException(
            message="Invalid credentials", message_code="invalid_credentials"
        )
    return role
