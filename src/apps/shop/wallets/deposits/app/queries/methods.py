"""Compose banking and hosted gateway options for a wallet top-up."""

from src.apps.shop.banking.payment_cards.app.interfaces.queries import (
    ICardPickQuery,
)
from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)
from src.apps.shop.crypto.gateways.app.interfaces.queries import (
    IGatewayMethodsQuery,
)
from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.dtos.methods import DepositMethods
from ...domain.results.methods import CardOption, PaymentOptions


class DepositMethodsQuery:
    def __init__(
        self,
        customers: ICustomerService,
        settings: IPaymentSettingsService,
        cards: ICardPickQuery,
        gateways: IGatewayMethodsQuery,
    ) -> None:
        """Bind the owners of customer, billing and gateway availability."""
        self.customers = customers
        self.settings = settings
        self.cards = cards
        self.gateways = gateways

    async def list(
        self, customer_id: int, data: DepositMethods
    ) -> PaymentOptions:
        """Read the methods offered for the customer's original rial amount.

        Args:
            customer_id: Identity of the customer requesting a top-up.
            data: Original amount in whole rials and gateway page selection.

        Returns:
            The card option when available and the matching gateway page.

        Raises:
            NotFoundException: The customer does not exist.
        """
        await self.customers.get_by_id(customer_id)
        settings = await self.settings.get()
        mode = (
            PaymentMode.AUTO if settings.auto_confirm else PaymentMode.MANUAL
        )
        card = CardOption(mode) if await self.cards.available(mode) else None
        gateways = await self.gateways.list(
            data.amount,
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        return PaymentOptions(
            customer_id=customer_id,
            amount=data.amount,
            card_to_card=card,
            gateways=gateways.items,
            total_gateways=gateways.total_items,
        )
