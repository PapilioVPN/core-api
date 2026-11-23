"""Materialized self-account view without stored credentials."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserProfileResult:
    """Current profile with role and scope snapshot from the access token."""

    id: int
    first_name: str
    last_name: str
    mobile: str
    email: str | None
    role_id: int
    is_super_admin: bool
    scopes: dict[str, int]
