"""Safe payment settings output and one-time key delivery."""

from papilio.schemas.outputs import BaseOutput


class PaymentSettingsOutput(BaseOutput):
    auto_confirm: bool
    digits: int
    window_hours: int
    has_key: bool


class PaymentKeyOutput(BaseOutput):
    key: str
