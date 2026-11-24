"""Pure role removal policy from authoritative user-reference facts."""

from papilio.errors.exceptions import ValidationException


def validate_role_removal(role_id: int, has_users: bool) -> None:
    """Reject removal while any account references the role.

    Args:
        role_id: Existing role identity checked by its owning service.
        has_users: Authoritative existence fact, including inactive accounts.

    Returns:
        None when the role has no user references.

    Raises:
        ValidationException: At least one account references this role.
    """
    if has_users:
        raise ValidationException(
            message="Cannot remove a role assigned to users",
            message_code="role_has_users",
            loc=["role_id"],
            input=role_id,
        )
