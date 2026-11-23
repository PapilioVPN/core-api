"""Trusted identity input and materialized token verification metadata."""

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import JsonValue


@dataclass(frozen=True, slots=True)
class TokenIdentity:
    """Account-owner identity and JSON claims, without an account-store link.

    subject is the owner's stable string identity. audience identifies the
    intended consumer; it is supplied by the owning application, not inferred
    from caller-provided claims. Each owner prepares its own claims explicitly.
    Role/scope construction and permission meaning remain with that owner.
    This carrier performs no HTTP validation and does not declare JWT layout.
    """

    subject: str
    audience: str
    claims: dict[str, JsonValue] = field(default_factory=dict, repr=False)


@dataclass(frozen=True, slots=True)
class VerifiedToken:
    """Identity and metadata after the requested token kind was verified.

    issued_at and expires_at are actual UTC-aware token timestamps. This result
    describes token verification; account eligibility and session/revocation
    policies remain separate owning responsibilities.
    """

    identity: TokenIdentity
    token_id: str
    issued_at: datetime
    expires_at: datetime
