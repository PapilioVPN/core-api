"""Private crypto integration settings keyed by the gateway account key."""

from papilio.types.aliases import SlugType
from pydantic import BaseModel, ConfigDict, Field

from .infra.nowpayments.config import NowPaymentsConfig


class CryptoPaymentsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nowpayments: dict[SlugType, NowPaymentsConfig] = Field(
        default_factory=dict
    )
