"""Calculate an invoice price from the gateway policy and latest rates."""

from datetime import timedelta
from decimal import Decimal

from papilio.errors.exceptions import ConflictException
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    IGatewayConfigService,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.rates.app.interfaces.cache import IRateCache
from src.apps.shop.crypto.rates.app.interfaces.services import (
    IConversionService,
)
from src.apps.shop.crypto.rates.domain.results.records import RateFailure

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel
from ...domain.policy import NOWPAYMENTS, PLISIO, RIAL, USD


class PaymentPricingService:
    def __init__(
        self,
        gateways: ICryptoGatewayService,
        configs: IGatewayConfigService,
        rates: IRateCache,
        conversion: IConversionService,
    ) -> None:
        """Bind account pricing and the shared rate conversion."""
        self.gateways = gateways
        self.configs = configs
        self.rates = rates
        self.conversion = conversion

    async def price(
        self, payment: CryptoPaymentModel, *, max_age: timedelta
    ) -> Quote | RateFailure:
        """Price the original rial amount in the gateway's currency.

        Args:
            payment: Original payment and issuing gateway identity.
            max_age: Maximum age of a rate observation.

        Returns:
            A quote or the reason the required observation cannot be used.

        Raises:
            ConflictException: The gateway does not support pricing.
        """
        gateway = await self.gateways.get_by_id(payment.gateway_id)
        match gateway.kind:
            case kind if kind == PLISIO:
                currency = await self.configs.plisio_price(gateway.id)
            case kind if kind == NOWPAYMENTS:
                currency = USD
            case _:
                raise ConflictException(
                    message="The gateway has no supported pricing currency.",
                    message_code="crypto_gateway_pricing_unsupported",
                    unique_dict={"kind": gateway.kind},
                )
        result: Quote | RateFailure = Quote(
            amount=Decimal(payment.amount), currency=RIAL
        )
        if currency == USD:
            rate = await self.rates.find(currency)
            if isinstance(rate, RateFailure):
                result = rate
            else:
                usd = self.conversion.to_usd(
                    payment.amount, rate, now=utc_now(), max_age=max_age
                )
                if isinstance(usd, RateFailure):
                    result = usd
                else:
                    result = Quote(
                        amount=usd.amount,
                        currency=currency,
                        rate=usd.rial_rate,
                    )
        return result
