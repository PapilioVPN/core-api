"""Account facts needed for live authorization."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserAccess:
    id: int
    role_id: int
    is_active: bool
    is_super_admin: bool
