"""Validate the options accepted by Variza's payment-link API."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from pydantic import Field, SecretStr, StringConstraints

type CardSelection = Annotated[
    str, StringConstraints(pattern=r"^(?:[0-9]{4}|random|variza)$")
]
type LinkExpiry = Literal["30m", "1h", "2h", "6h", "1d", "3d", "1w", "never"]


class VarizaLinkConfig(BaseDTO):
    api_key: SecretStr = Field(min_length=1, repr=False)
    card_last_4: CardSelection | None = None
    expires_in: LinkExpiry | None = None


class VarizaConfig(VarizaLinkConfig):
    webhook_secret: SecretStr = Field(min_length=1, repr=False)
