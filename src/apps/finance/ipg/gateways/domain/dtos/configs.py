"""Accept the merchant credential provided by the payment provider."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from pydantic import ConfigDict, Field, Secret, StringConstraints

type MerchantId = Annotated[
    str,
    StringConstraints(
        strict=True, min_length=1, max_length=255, pattern=r"^\S+$"
    ),
]


class GatewayConfig(BaseDTO):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    merchant_id: Secret[MerchantId] = Field(repr=False)
