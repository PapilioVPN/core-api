"""Bank reference output for the administrator panel."""

from papilio.schemas.outputs import BaseOutput


class BankOutput(BaseOutput):
    id: int
    code: str
    title: str
    icon_url: str | None
    is_active: bool
    priority: int


class BankMatchOutput(BankOutput):
    is_prefix_active: bool
