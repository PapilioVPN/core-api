"""Private deployment settings for one NOWPayments merchant account."""

from typing import Annotated

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    UrlConstraints,
)

HTTPSURL = Annotated[
    AnyUrl, UrlConstraints(allowed_schemes=["https"], host_required=True)
]


class NowPaymentsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    api_url: HTTPSURL
    callback_base_url: HTTPSURL
    api_key: SecretStr = Field(min_length=1, repr=False)
    ipn_secret: SecretStr = Field(min_length=1, repr=False)
    price_decimals: int = Field(ge=0, le=18)
