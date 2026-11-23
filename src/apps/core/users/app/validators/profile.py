"""Pure self-account eligibility, ownership and contact-edit policies."""

from papilio.errors.exceptions import (
    ForbiddenException,
    UnAuthorizedException,
    ValidationException,
)

from src.apps.core.roles.domain.models.records import RoleModel
from src.apps.core.users.domain.dtos.records import UserUpdate
from src.apps.core.users.domain.models.records import UserModel


def require_active_user(user: UserModel | None) -> UserModel:
    """Require an available account for self-profile access.

    Args:
        user: Authoritative user lookup result, or None when missing.

    Returns:
        The unchanged active account.

    Raises:
        UnAuthorizedException: The account is absent or inactive.
    """
    if user is None or not user.is_active:
        raise UnAuthorizedException(
            message="Account is unavailable",
            message_code="account_unavailable",
        )
    return user


def require_active_role(
    role: RoleModel | None, *, super_admin: bool = False
) -> RoleModel:
    """Require an available assigned role for self-profile access.

    Args:
        role: Authoritative current role, or None when missing.

    Returns:
        The unchanged active role.

    Raises:
        UnAuthorizedException: The assigned role is absent or inactive.
    """
    if role is None or (not role.is_active and not super_admin):
        raise UnAuthorizedException(
            message="Account is unavailable",
            message_code="account_unavailable",
        )
    return role


def validate_self_account(user_id: int, target_id: int) -> None:
    """Require the path target to match the authenticated self account.

    Args:
        user_id: Internal account ID from verified access and sudo.
        target_id: Positive target ID from the HTTP path.

    Returns:
        None when the two identities match.

    Raises:
        ForbiddenException: The caller targets a different account.
    """
    if user_id != target_id:
        raise ForbiddenException(
            message="Only your own account is allowed",
            message_code="self_account_required",
        )


def protect_owner(user: UserModel) -> None:
    """Protect the bootstrap administrator from destructive account edits."""
    if user.is_super_admin:
        raise ForbiddenException(
            message="The Super Admin account is protected",
            message_code="super_admin_protected",
        )


def validate_contact_fields(data: UserUpdate) -> None:
    """Keep contact changes disabled until their verification flow exists.

    Args:
        data: Validated general account patch with native field presence.

    Returns:
        None when mobile and email were omitted; explicit null is supplied.

    Raises:
        ValidationException: The patch supplies either contact field.
    """
    if {"mobile", "email"} & data.model_fields_set:
        raise ValidationException(
            message="Contact updates require a separate verification flow",
            message_code="contact_update_unavailable",
            loc=[],
        )
