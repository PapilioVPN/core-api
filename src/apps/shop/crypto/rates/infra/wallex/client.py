"""Read one USDT price through Papilio's shared HTTP pool."""

from decimal import Decimal

from httpx import HTTPError
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from ...domain.results.records import RateFailure
from .schemas import MarketsResponse


class WallexRateGateway(BaseGateway):
    __base_url__ = "https://api.wallex.ir/v1"

    async def read(self) -> Decimal | RateFailure:
        """Read the last USDT trade in tomans from the public market.

        Returns:
            The market price in tomans per USDT, or the failure reason.
        """
        try:
            response = await self.get("/markets")
            response.raise_for_status()
            market = MarketsResponse.model_validate_json(response.content)
        except HTTPError:
            result = RateFailure.MARKET_UNAVAILABLE
        except ValidationError:
            result = RateFailure.INVALID_RATE
        else:
            result = market.market.stats.last_price
        return result
