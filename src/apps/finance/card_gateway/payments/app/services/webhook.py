"""Authenticate one gateway account and read its verified notification."""

from papilio.errors.exceptions import UnAuthorizedException

from ....gateways.app.interfaces.configs import IGatewayConfigService
from ...domain.dtos.paid import PaidDelivery
from ..interfaces.webhook import IVarizaWebhookCodec


class VarizaWebhookService:
    def __init__(
        self,
        configs: IGatewayConfigService,
        codec: IVarizaWebhookCodec,
    ) -> None:
        self.configs = configs
        self.codec = codec

    async def read(
        self,
        gateway_id: int,
        delivery_id: str,
        body: bytes,
        signature: str | None,
    ) -> PaidDelivery | None:
        """Verify the raw notification and materialize its paid evidence.

        Args:
            gateway_id: Account identified by the webhook path.
            delivery_id: Validated provider delivery identity from the header.
            body: Exact bytes read at the webhook boundary.
            signature: Signature presented by the provider, if supplied.

        Returns:
            Authenticated paid evidence in whole rials, or None for an
            authenticated event that does not confirm a payment.

        Raises:
            UnAuthorizedException: The gateway or signature is invalid.
            ValidationException: The authenticated body is malformed.
        """
        secret = await self.configs.webhook(gateway_id)
        if (
            signature is None
            or secret is None
            or not self.codec.valid_signature(body, signature, secret)
        ):
            raise UnAuthorizedException(
                message="Invalid Variza notification signature.",
                message_code="variza_webhook_signature_invalid",
            )
        transfer = self.codec.read_paid(body)
        delivery = (
            PaidDelivery(gateway_id, delivery_id, transfer)
            if transfer is not None
            else None
        )
        return delivery
