"""Issue a payment link using Zibal's v1 protocol."""

from httpx import ConnectError, ConnectTimeout, PoolTimeout, RequestError
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from ...domain.enums.records import LinkStatus
from ...domain.results.link import LinkRequest, ProviderLink
from .payload import LinkPayload

_PAY_URL = "https://gateway.zibal.ir/start"
_ACCEPTED = 100


class ZibalClient(BaseGateway):
    __base_url__ = "https://gateway.zibal.ir/v1"

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
                "/request",
                json={
                    "merchant": request.merchant_id.get_secret_value(),
                    "amount": request.amount,
                    "description": request.description,
                    "callbackUrl": request.callback_url,
                    "orderId": str(request.payment_id),
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
            if payload.result != _ACCEPTED:
                result = ProviderLink(LinkStatus.REJECTED)
            elif success and payload.trackId is not None:
                reference = str(payload.trackId)
                result = ProviderLink(
                    LinkStatus.READY, reference, f"{_PAY_URL}/{reference}"
                )
        return result
