"""Issue a wallet top-up invoice for an existing customer."""

from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.dtos.records import DepositCreate
from ...domain.models.records import DepositInvoice
from ..interfaces.services import IWalletDepositService


class WalletDepositCommand:
    def __init__(
        self, customers: ICustomerService, deposits: IWalletDepositService
    ) -> None:
        """Bind the customer lookup and the invoice service."""
        self.customers = customers
        self.deposits = deposits

    async def issue(
        self, customer_id: int, data: DepositCreate
    ) -> DepositInvoice:
        """Issue an initial invoice with the requested rial amount.

        Args:
            customer_id: Identity of the customer requesting the top-up.
            data: Validated positive top-up amount in whole rials.

        Returns:
            The cached invoice with its expiration.

        Raises:
            NotFoundException: The customer does not exist.
            DepositInvoiceUnavailable: The invoice could not be stored.
        """
        await self.customers.get_by_id(customer_id)
        invoice = await self.deposits.create(customer_id, data.amount)
        return invoice
