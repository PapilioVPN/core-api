"""Validate the selected USDT market from the Wallex response."""

from decimal import Decimal
from typing import Literal

from pydantic import AliasPath, BaseModel, Field


class MarketStats(BaseModel):
    last_price: Decimal = Field(
        validation_alias="lastPrice", gt=0, allow_inf_nan=False, max_digits=28
    )


class Market(BaseModel):
    base_asset: Literal["USDT"] = Field(validation_alias="baseAsset")
    quote_asset: Literal["TMN"] = Field(validation_alias="quoteAsset")
    stats: MarketStats


class MarketsResponse(BaseModel):
    success: Literal[True]
    market: Market = Field(
        validation_alias=AliasPath("result", "symbols", "USDTTMN")
    )
