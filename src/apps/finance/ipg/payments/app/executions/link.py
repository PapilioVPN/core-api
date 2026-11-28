"""Commit payment terms and link evidence in independent SQL phases."""

from dishka import AsyncContainer
from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from ....gateways.app.interfaces.configs import IGatewayConfigService
from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ...domain.results.link import LinkRequest, PaymentLink, ProviderLink
from ..interfaces.services import IPaymentService


class LinkExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def prepare(
        self,
        data: PaymentCreate,
        *,
        configs: IGatewayConfigService = Inject(),
        payments: IPaymentService = Inject(),
    ) -> LinkRequest:
        """Commit one payment before contacting the selected provider.

        Args:
            data: Trusted payment terms in whole rials.
            configs: Authoritative gateway configuration service.
            payments: Scoped payment record service.

        Returns:
            The materialized request to send after committing.

        Raises:
            ValidationException: The provider is inactive or unavailable.
        """
        merchant = await configs.merchant(data.kind)
        if merchant is None:
            raise ValidationException(
                message="The selected gateway is unavailable.",
                message_code="ipg_gateway_unavailable",
                loc=["kind"],
            )
        payment = await payments.create(
            PaymentModel(
                gateway_id=merchant.gateway_id,
                amount=data.amount,
                description=data.description,
                credential=merchant.token,
            )
        )
        return LinkRequest(
            payment.id,
            merchant.id,
            data.amount,
            data.description,
            str(data.callback_url),
        )

    @request_scoped
    @transactional
    async def finish(
        self,
        id: int,
        link: ProviderLink,
        *,
        payments: IPaymentService = Inject(),
    ) -> PaymentLink:
        """Commit the observed outcome and return it to the caller.

        Args:
            id: Payment identity committed before dispatch.
            link: Observed provider response or classified failure.
            payments: Scoped payment record service.

        Returns:
            The stored issuance status and redirect URL if issued.
        """
        payment = await payments.save_link(id, link)
        result = PaymentLink(
            payment.id, payment.status, payment.pay_url, payment.reference
        )
        return result
