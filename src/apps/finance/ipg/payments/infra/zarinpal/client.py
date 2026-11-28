"""Issue a payment link using the ZarinPal v4 protocol."""

from httpx import ConnectError, ConnectTimeout, PoolTimeout, RequestError
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from ...domain.enums.records import LinkStatus
from ...domain.results.link import LinkRequest, ProviderLink
from .payload import ErrorData, LinkData, LinkPayload

_PAY_URL = "https://payment.zarinpal.com/pg/StartPay"
_ACCEPTED = 100


class ZarinPalClient(BaseGateway):
    __base_url__ = "https://payment.zarinpal.com/pg/v4/payment"

    def __init__(self, connection: HTTPConnection) -> None:
        super().__init__(connection)

    async def create(self, request: LinkRequest) -> ProviderLink:
        """Request a redirect for the exact amount in whole rials.

        Args:
            request: Prepared payment with its merchant and callback URL.

        Returns:
            The provider link, a known failure, or an unresolved outcome.
        """
        result = ProviderLink(LinkStatus.UNKNOWN)
        try:
            response = await self.post(
                "/request.json",
                json={
                    "merchant_id": request.merchant_id.get_secret_value(),
                    "amount": request.amount,
                    "currency": "IRR",
                    "description": request.description,
                    "callback_url": request.callback_url,
                },
            )
            if response.is_success or 400 <= response.status_code < 500:
                result = self._link(response.content, response.is_success)
        except (ConnectError, ConnectTimeout, PoolTimeout):
            result = ProviderLink(LinkStatus.UNAVAILABLE)
        except RequestError:
            pass
        return result

    def _link(self, content: bytes, success: bool) -> ProviderLink:
        """Translate a documented response without retaining provider data."""
        result = ProviderLink(LinkStatus.UNKNOWN)
        try:
            payload = LinkPayload.model_validate_json(content)
        except ValidationError:
            pass
        else:
            data, errors = payload.data, payload.errors
            match data, errors:
                case _, ErrorData(code=code) if code < 0:
                    result = ProviderLink(LinkStatus.REJECTED)
                case LinkData(code=code, authority=authority), _ if (
                    code == _ACCEPTED and success and authority is not None
                ):
                    result = ProviderLink(
                        LinkStatus.READY, authority, f"{_PAY_URL}/{authority}"
                    )
        return result
