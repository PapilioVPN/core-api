"""Typed inputs for a complete gateway configuration replacement."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from pydantic import ConfigDict, Field, SecretStr, TypeAdapter, field_validator

from src.apps.shop.crypto.types import HTTPSURL


class GatewayConfig(BaseDTO):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    callback_base_url: HTTPSURL
    api_key: SecretStr = Field(min_length=1, repr=False)
    price_decimals: int = Field(ge=0, le=18)

    @field_validator("callback_base_url")
    @classmethod
    def check_base_url(cls, value: HTTPSURL) -> HTTPSURL:
        """Allow a public HTTPS root without credentials, query or fragment."""
        if (
            value.username is not None
            or value.password is not None
            or value.query is not None
            or value.fragment is not None
        ):
            raise ValueError("A clean HTTPS callback base URL is required")
        return value


class NowPaymentsConfig(GatewayConfig):
    kind: Literal["nowpayments"]
    api_url: Literal[
        "https://api.nowpayments.io/v1",
        "https://api-sandbox.nowpayments.io/v1",
    ]
    ipn_secret: SecretStr = Field(min_length=1, repr=False)


class PlisioConfig(GatewayConfig):
    kind: Literal["plisio"]
    api_url: Literal["https://api.plisio.net/api/v1"]


ConfigWrite = Annotated[
    NowPaymentsConfig | PlisioConfig, Field(discriminator="kind")
]
config_adapter: TypeAdapter[ConfigWrite] = TypeAdapter(ConfigWrite)
