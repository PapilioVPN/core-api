"""An issued API key and its one-time plaintext value."""

from dataclasses import dataclass, field

from ..models.records import APIKeyModel


@dataclass(frozen=True, slots=True)
class IssuedAPIKey:
    api_key: APIKeyModel
    key: str = field(repr=False)
