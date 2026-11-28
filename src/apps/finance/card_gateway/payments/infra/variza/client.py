"""Create payment links against Variza's v1 HTTP API."""

from http import HTTPStatus

from httpx import ConnectError, ConnectTimeout, PoolTimeout, RequestError
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway
from pydantic import HttpUrl, JsonValue, ValidationError

from ...domain.results.link import Link, LinkFailure, LinkRequest, LinkResult
from .payload import RIALS_PER_TOMAN, LinkPayload

_HOST = "variza.ir"
_MINIMUM_TOMAN = 1_000


class VarizaClient(BaseGateway):
    __base_url__ = f"https://{_HOST}/api/v1"

    def __init__(self, connection: HTTPConnection) -> None:
        super().__init__(connection)

    async def create(
        self, request: LinkRequest, return_url: HttpUrl
    ) -> LinkResult:
        """Request one hosted link for an exact integer amount in tomans.

        Args:
            request: Trusted amount in rials and the selected account settings.
            return_url: Trusted destination for the buyer's return.

        Returns:
            The provider link, a definitive failure, or UNKNOWN if a request
            may already have created a link.
        """
        amount, remainder = divmod(request.amount, RIALS_PER_TOMAN)
        if remainder or amount < _MINIMUM_TOMAN:
            result = LinkResult(failure=LinkFailure.INVALID_AMOUNT)
        elif return_url.scheme != "https":
            result = LinkResult(failure=LinkFailure.INVALID_RETURN_URL)
        else:
            result = await self._post_link(request, amount, return_url)
        return result

    async def _post_link(
        self, request: LinkRequest, amount: int, return_url: HttpUrl
    ) -> LinkResult:
        """Send the validated provider request and classify its outcome.

        Args:
            request: Account credentials and optional link settings.
            amount: Exact whole tomans accepted by the provider.
            return_url: Trusted HTTPS destination for the buyer.

        Returns:
            A parsed link or a typed failure without response data or secrets.
        """
        config = request.config
        data: dict[str, JsonValue] = {
            "amount": amount,
            "return_url": str(return_url),
        }
        if config.card_last_4 is not None:
            data["card_last_4"] = config.card_last_4
        if config.expires_in is not None:
            data["expires_in"] = config.expires_in
        api_key = config.api_key.get_secret_value()
        result = LinkResult(failure=LinkFailure.UNKNOWN)
        try:
            response = await self.post(
                "/pay",
                headers={"Authorization": f"Bearer {api_key}"},
                json=data,
            )
        except (ConnectError, ConnectTimeout, PoolTimeout):
            result = LinkResult(failure=LinkFailure.UNAVAILABLE)
        except UnicodeEncodeError:
            result = LinkResult(failure=LinkFailure.REJECTED)
        except RequestError:
            pass
        else:
            if response.status_code == HTTPStatus.CREATED:
                try:
                    payload = LinkPayload.model_validate_json(response.content)
                except ValidationError:
                    pass
                else:
                    if (
                        payload.amount == amount
                        and payload.pay_url.scheme == "https"
                        and payload.pay_url.host == _HOST
                    ):
                        result = LinkResult(
                            link=Link(
                                payload.slug,
                                str(payload.pay_url),
                                payload.expires_at,
                            )
                        )
            elif response.status_code in (
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.UNPROCESSABLE_ENTITY,
            ):
                result = LinkResult(failure=LinkFailure.REJECTED)
            elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                result = LinkResult(failure=LinkFailure.UNAVAILABLE)
        return result
