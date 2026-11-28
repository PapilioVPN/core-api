"""Policy fields shown to Finance operators."""

from papilio.schemas.outputs import BaseOutput


class TransferSettingsOutput(BaseOutput):
    auto_confirm: bool
    digits: int
    window_minutes: int | None
