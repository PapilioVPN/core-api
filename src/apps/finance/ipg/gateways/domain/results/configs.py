"""Merchant credentials for a selected gateway."""

from dataclasses import dataclass

from pydantic import SecretStr


@dataclass(frozen=True, slots=True)
class Merchant:
    gateway_id: int
    id: SecretStr
