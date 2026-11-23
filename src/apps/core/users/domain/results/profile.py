"""Materialized self-account view without stored credentials."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserProfileResult:
    """Current profile with the latest authenticated role and scopes."""

    id: int
    first_name: str
    last_name: str
    mobile: str
    email: str | None
    role_id: int
    is_super_admin: bool
    scopes: dict[str, int]
