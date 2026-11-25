"""Receive a bank report and queue its payment match."""

from hashlib import sha256
from secrets import compare_digest

from papilio.core.resources import INVALID_TOKEN
from papilio.errors.exceptions import UnAuthorizedException
from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter
from papilio_tasks.apps.outbox import decorators as outbox

from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)

from ...domain.dtos.records import DepositCreate
from ...domain.events.records import DepositReceived
from ...domain.models.records import DepositModel
from ...infra.broker.publishers import deposit_received
from ..interfaces.services import IDepositService


class DepositCommand:
    def __init__(
        self,
        settings: IPaymentSettingsService,
        deposits: IDepositService,
        outbox: OutboxWriter,
    ) -> None:
        """Bind the payment policy and deposit operations."""
        self.settings = settings
        self.deposits = deposits
        self.outbox = outbox

    @transactional
    @outbox.publish(deposit_received, select=DepositReceived.from_record)
    async def receive(
        self, data: DepositCreate, key: str | None
    ) -> DepositModel:
        """Register a bank report and its event in one transaction.

        Args:
            data: Exact rial amount and optional time supplied by the bank.
            key: Webhook key supplied by the configured bank sender.

        Returns:
            The stored deposit awaiting an automatic match.

        Raises:
            UnAuthorizedException: The hook key is absent, invalid or revoked.
        """
        settings = await self.settings.get()
        if (
            key is None
            or settings.key_hash is None
            or not compare_digest(
                sha256(key.encode()).hexdigest(), settings.key_hash
            )
        ):
            raise UnAuthorizedException(
                "Invalid bank webhook key", INVALID_TOKEN
            )
        record = await self.deposits.create(
            DepositModel(amount=data.amount, paid_at=data.paid_at)
        )
        return record
