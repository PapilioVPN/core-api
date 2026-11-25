"""Match received deposits to automatic payments in the active window."""

from datetime import datetime, timedelta
from typing import cast

from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)
from src.apps.shop.billing.payments.app.interfaces.commands import (
    IPaymentReviewCommand,
)

from ...domain.models.records import DepositModel
from ..interfaces.services import IDepositService


class DepositMatchCommand:
    def __init__(
        self,
        deposits: IDepositService,
        settings: IPaymentSettingsService,
        payments: IPaymentReviewCommand,
    ) -> None:
        """Bind the record and review owners to the worker request."""
        self.deposits = deposits
        self.settings = settings
        self.payments = payments

    @transactional
    async def match(self, id: int) -> DepositModel:
        """Confirm at most one payment and link it to the deposited funds.

        Args:
            id: Stored deposit identity delivered by Events.

        Returns:
            The deposit with its current payment link, if any.
        """
        deposit = await self.deposits.get(id)
        if deposit.payment_id is None:
            settings = await self.settings.get()
            if settings.auto_confirm:
                # PostgreSQL supplies the non-null timestamp when inserting.
                received_at = cast(datetime, deposit.created_at)
                since = received_at - timedelta(hours=settings.window_hours)
                until = min(received_at, deposit.paid_at or received_at)
                payment = await self.payments.confirm_auto(
                    deposit.amount, since=since, until=until
                )
                if payment is not None:
                    deposit = await self.deposits.link(deposit.id, payment.id)
        return deposit
