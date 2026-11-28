"""Run one provider request between committed database phases."""

from ....gateways.domain.enums.records import GatewayKind
from ...domain.dtos.records import PaymentCreate
from ...domain.results.link import PaymentLink
from ..interfaces.create import ILinkExecution, IZarinPalClient, IZibalClient


class CreatePaymentCommand:
    def __init__(
        self,
        execution: ILinkExecution,
        zarinpal: IZarinPalClient,
        zibal: IZibalClient,
    ) -> None:
        self.execution = execution
        self.clients = {
            GatewayKind.ZARINPAL: zarinpal,
            GatewayKind.ZIBAL: zibal,
        }

    async def create(self, data: PaymentCreate) -> PaymentLink:
        """Issue one payment link for a trusted calling service.

        Args:
            data: Selected gateway, amount in whole rials and callback URL.

        Returns:
            Payment identity and the committed provider outcome.
        """
        request = await self.execution.prepare(data)
        link = await self.clients[data.kind].create(request)
        result = await self.execution.finish(request.payment_id, link)
        return result
