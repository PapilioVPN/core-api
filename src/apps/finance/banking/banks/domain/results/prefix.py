"""The issuer and current status of its matching card prefix."""

from dataclasses import dataclass

from ..models.records import BankModel


@dataclass(frozen=True, slots=True)
class BankMatch:
    bank: BankModel
    is_prefix_active: bool
