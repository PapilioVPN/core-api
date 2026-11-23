"""Administrator identity resolved from a token and current access state."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AdminIdentity:
    """Authenticated account, active session and current permissions."""

    user_id: int
    role_id: int
    scopes: dict[str, int]
    session_id: UUID
    is_super_admin: bool
