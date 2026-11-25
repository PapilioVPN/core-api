"""Cache-safe projection of the current payment settings."""

from dataclasses import dataclass
from typing import Self

from ..models.records import PaymentSettingsModel


@dataclass(frozen=True, slots=True)
class PaymentSettingsView:
    auto_confirm: bool
    digits: int
    window_hours: int
    has_key: bool

    @classmethod
    def from_record(cls, record: PaymentSettingsModel) -> Self:
        return cls(
            record.auto_confirm,
            record.digits,
            record.window_hours,
            record.key_hash is not None,
        )
