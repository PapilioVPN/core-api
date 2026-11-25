"""Freeze the invoice price on a local payment."""

from datetime import timedelta
from decimal import Decimal

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    IGatewayConfigService,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.models.records import (
    CryptoGatewayModel,
)
from src.apps.shop.crypto.rates.app.interfaces.cache import IRateCache
from src.apps.shop.crypto.rates.app.interfaces.services import (
    IConversionService,
)

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel
from ..interfaces.services import ICryptoPaymentService


class PaymentQuoteCommand:
    def __init__(
        self,
        payments: ICryptoPaymentService,
        gateways: ICryptoGatewayService,
        configs: IGatewayConfigService,
        rates: IRateCache,
        conversion: IConversionService,
    ) -> None:
        """Bind authoritative reads, pure conversion and payment writes."""
        self.payments = payments
        self.gateways = gateways
        self.configs = configs
        self.rates = rates
        self.conversion = conversion

    @transactional
    async def quote(
        self, id: int, *, max_age: timedelta
    ) -> CryptoPaymentModel:
        """Save the invoice quote once, before making any provider call.

        Args:
            id: The stored payment identity.
            max_age: Oldest acceptable Wallex observation for USD pricing.

        Returns:
            The payment with its original quote.

        Raises:
            NotFoundException: The payment or its gateway is missing.
            RateUnavailable: USD pricing has no usable fresh rate.
            ConflictException: Pricing is unsupported or another write won.
        """
        payment = await self.payments.get_by_id(id)
        if payment.quote_amount is None:
            gateway = await self.gateways.get_by_id(payment.gateway_id)
            data = await self._price(payment.amount, gateway, max_age)
            saved = await self.payments.set_quote(id, data)
            if saved is None:
                raise ConflictException(
                    message="The payment quote has already been saved.",
                    message_code="crypto_payment_quote_exists",
                    unique_dict={"payment_id": id},
                )
            payment = saved
        return payment

    async def _price(
        self, amount: int, gateway: CryptoGatewayModel, max_age: timedelta
    ) -> Quote:
        """Select the provider's pricing currency and prepare its amount."""
        match gateway.kind:
            case "plisio":
                currency = await self.configs.plisio_price(gateway.id)
            case "nowpayments":
                currency = "USD"
            case _:
                raise ConflictException(
                    message="The gateway has no supported pricing currency.",
                    message_code="crypto_gateway_pricing_unsupported",
                    unique_dict={"kind": gateway.kind},
                )
        if currency == "USD":
            rate = await self.rates.find("USD")
            usd = self.conversion.to_usd(
                amount, rate, now=utc_now(), max_age=max_age
            )
            quote = Quote(
                amount=usd.amount, currency="USD", rate=usd.rial_rate
            )
        else:
            quote = Quote(amount=Decimal(amount), currency="IRR")
        return quote
