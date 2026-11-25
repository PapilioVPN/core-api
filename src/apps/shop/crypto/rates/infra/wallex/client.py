"""Read one USDT price through Papilio's shared HTTP pool."""

from decimal import Decimal

from httpx import HTTPError
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from ...domain.errors import RateUnavailable
from .schemas import MarketsResponse


class WallexRateGateway(BaseGateway):
    __base_url__ = "https://api.wallex.ir/v1"

    async def read(self) -> Decimal:
        """Read the last USDT trade in tomans from the public market.

        Returns:
            The positive market price in tomans per USDT.

        Raises:
            RateUnavailable: Wallex failed or returned an unusable price.
        """
        try:
            response = await self.get("/markets")
            response.raise_for_status()
            market = MarketsResponse.model_validate_json(response.content)
        except (HTTPError, ValidationError):
            raise RateUnavailable() from None
        return market.market.stats.last_price
