"""Commit link creation claims and results in short native SQL phases."""

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now

from ....gateways.app.interfaces.configs import IGatewayConfigService
from ...domain.results.link import (
    Link,
    LinkFailure,
    LinkPreparation,
    LinkRequest,
    LinkResult,
)
from ...infra.pg.repositories.crud import PaymentRepository


class LinkExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def prepare(
        self,
        id: int,
        *,
        payments: PaymentRepository = Inject(),
        configs: IGatewayConfigService = Inject(),
    ) -> LinkPreparation:
        """Read a valid existing link or claim a new outbound attempt.

        Args:
            id: Committed payment identity.
            payments: Request-scoped payment repository.
            configs: Authoritative link settings.

        Returns:
            The current result and dispatch terms in rials when this
            operation owns a new attempt.
        """
        payment = await payments.get_by_id(id)
        now = utc_now()
        request = None
        if payment is None:
            result = LinkResult(failure=LinkFailure.NOT_FOUND)
        elif payment.slug is not None and payment.pay_url is not None:
            if payment.expires_at is not None and payment.expires_at <= now:
                result = LinkResult(failure=LinkFailure.EXPIRED)
            else:
                result = LinkResult(
                    link=Link(
                        payment.slug, payment.pay_url, payment.expires_at
                    )
                )
        elif payment.link_requested_at is not None:
            result = LinkResult(failure=LinkFailure.UNKNOWN)
        else:
            config = await configs.link(payment.gateway_id)
            if config is None:
                result = LinkResult(failure=LinkFailure.GATEWAY_UNAVAILABLE)
            else:
                claimed = await payments.claim_link(id, requested_at=now)
                result = LinkResult(failure=LinkFailure.UNKNOWN)
                if claimed:
                    request = LinkRequest(payment.amount, config)
        return LinkPreparation(result=result, request=request)

    @request_scoped
    @transactional
    async def finish(
        self,
        id: int,
        result: LinkResult,
        *,
        payments: PaymentRepository = Inject(),
    ) -> LinkResult:
        """Persist a confirmed link or release a definitively failed claim.

        Args:
            id: Payment identity with a committed dispatch claim.
            result: Typed provider outcome of this attempt.
            payments: Request-scoped payment repository.

        Returns:
            The committed link or the applicable failure.
        """
        link = result.link
        if link is not None:
            payment = await payments.save_link(
                id,
                slug=link.slug,
                pay_url=link.pay_url,
                expires_at=link.expires_at,
            )
            if payment is None:
                result = LinkResult(failure=LinkFailure.UNKNOWN)
        elif result.failure is not LinkFailure.UNKNOWN:
            released = await payments.release_link(id)
            if not released:
                result = LinkResult(failure=LinkFailure.UNKNOWN)
        return result
