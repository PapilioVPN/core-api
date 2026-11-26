"""Freeze the invoice price on a local payment."""

from datetime import timedelta

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional

from ...domain.models.records import CryptoPaymentModel
from ..interfaces.services import ICryptoPaymentService, IPaymentPricingService


class PaymentQuoteCommand:
    def __init__(
        self, payments: ICryptoPaymentService, pricing: IPaymentPricingService
    ) -> None:
        """Bind payment records and the owner of invoice pricing."""
        self.payments = payments
        self.pricing = pricing

    @transactional
    async def quote(
        self, id: int, *, max_age: timedelta
    ) -> CryptoPaymentModel:
        """Save the invoice quote once, before making any provider call.

        Args:
            id: Stored payment identity.
            max_age: Maximum age of a rate observation.

        Returns:
            The payment with its frozen quote.

        Raises:
            NotFoundException: The payment or its gateway does not exist.
            RateUnavailable: The needed rate is missing or stale.
            ConflictException: Pricing is unsupported or another write won.
        """
        payment = await self.payments.get_by_id(id)
        if payment.quote_amount is None:
            quote = await self.pricing.price(payment, max_age=max_age)
            saved = await self.payments.set_quote(id, quote)
            if saved is None:
                raise ConflictException(
                    message="The payment quote has already been saved.",
                    message_code="crypto_payment_quote_exists",
                    unique_dict={"payment_id": id},
                )
            payment = saved
        return payment
