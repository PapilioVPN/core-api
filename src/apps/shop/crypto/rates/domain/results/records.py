"""Expected failures when reading or converting a pricing rate."""

from enum import StrEnum


class RateFailure(StrEnum):
    INVALID_AMOUNT = "invalid_amount"
    MISSING_RATE = "missing_rate"
    INVALID_RATE = "invalid_rate"
    STALE_RATE = "stale_rate"
    MARKET_UNAVAILABLE = "market_unavailable"
    CACHE_UNAVAILABLE = "cache_unavailable"
    QUEUE_UNAVAILABLE = "queue_unavailable"
