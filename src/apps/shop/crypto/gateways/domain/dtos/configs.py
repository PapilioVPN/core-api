"""Validate connection settings for supported gateway providers."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from pydantic import ConfigDict, Field, SecretStr

type PriceCurrency = Literal["IRR", "USD"]


class GatewayConfig(BaseDTO):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    api_key: Annotated[
        SecretStr, Field(min_length=1, max_length=4096, repr=False)
    ]


class NowPaymentsConfig(GatewayConfig):
    kind: Literal["nowpayments"]
    api_url: Literal[
        "https://api.nowpayments.io/v1",
        "https://api-sandbox.nowpayments.io/v1",
    ]
    ipn_secret: Annotated[
        SecretStr, Field(min_length=1, max_length=4096, repr=False)
    ]


class PlisioConfig(GatewayConfig):
    kind: Literal["plisio"]
    api_url: Literal["https://api.plisio.net/api/v1"]
    price_currency: PriceCurrency = "IRR"


ConfigWrite = Annotated[
    NowPaymentsConfig | PlisioConfig, Field(discriminator="kind")
]
