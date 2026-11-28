"""Own the native SQL phases of scheduled IPG verification."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from ....gateways.domain.enums.records import GatewayKind
from ...domain.dtos.verify import VerifyPolicy
from ...domain.events.records import PaymentConfirmed
from ...domain.models.records import PaymentModel
from ...domain.results.verify import CheckTarget
from ...infra.broker.publishers import payment_confirmed
from ...infra.pg.repositories.verify import VerifyRepository


class VerifyExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def claim(
        self, policy: VerifyPolicy, *, repo: VerifyRepository = Inject()
    ) -> tuple[CheckTarget, ...]:
        """Commit the bounded reservation before SDK requests start."""
        now = utc_now()
        targets = await repo.claim(
            now=now,
            since=now - timedelta(minutes=policy.window_minutes),
            retry_at=now + timedelta(seconds=policy.retry_seconds),
            limit=policy.limit,
        )
        return targets

    @request_scoped
    @transactional
    async def find(
        self,
        kind: GatewayKind,
        reference: str,
        *,
        repo: VerifyRepository = Inject(),
    ) -> CheckTarget | None:
        """Materialize the stored callback terms before contacting the SDK."""
        target = await repo.find(kind, reference)
        return target

    @request_scoped
    @transactional
    async def confirm(
        self,
        id: int,
        code: str,
        *,
        repo: VerifyRepository = Inject(),
        outbox: OutboxWriter = Inject(),
    ) -> PaymentModel | None:
        """Commit the bank reference and identity event together."""
        payment = await repo.confirm(id, code=code, now=utc_now())
        if payment is not None:
            await outbox.append(
                payment_confirmed, PaymentConfirmed(payment_id=payment.id)
            )
        return payment
