"""Self-profile HTTP output with the existing user-ID mapping."""

from papilio.schemas.outputs import BaseOutput


class UserProfileOutput(BaseOutput):
    id: int
    first_name: str
    last_name: str
    mobile: str
    email: str | None
    role_id: int
    is_super_admin: bool
    scopes: dict[str, int]
