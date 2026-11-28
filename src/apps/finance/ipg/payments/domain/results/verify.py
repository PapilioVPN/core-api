"""Terms and outcomes of bounded payment verification."""

from dataclasses import dataclass

from pydantic import SecretStr

from ....gateways.domain.enums.records import GatewayKind


@dataclass(frozen=True, slots=True)
class CheckTarget:
    id: int
    kind: GatewayKind
    amount: int
    reference: str
    credential: str


@dataclass(frozen=True, slots=True)
class Verification:
    id: int
    amount: int
    reference: str
    merchant_id: SecretStr


@dataclass(frozen=True, slots=True)
class VerifyBatch:
    selected: int
    confirmed: int
