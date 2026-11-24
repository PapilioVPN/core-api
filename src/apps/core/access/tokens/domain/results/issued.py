"""Trusted token issuance result; credentials stay out of representations."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """One encoded credential and its actual UTC-aware expiration."""

    token: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Issued credentials and their actual absolute UTC-aware expirations.

    Access and refresh expire independently according to the owning configured
    policy. This contract supplies no lifetime, algorithm or secret default.
    """

    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    access_expires_at: datetime
    refresh_expires_at: datetime
