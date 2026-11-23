"""Account identity materialized from a verified administrator token."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdminIdentity:
    """Verified token identity and permissions; owners check eligibility."""

    user_id: int
    role_id: int
    scopes: dict[str, int]
