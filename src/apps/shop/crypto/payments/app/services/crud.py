"""Persist cryptocurrency payment records."""

from papilio.tools.checks import IDChecks

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel
from ...infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentService(IDChecks[CryptoPaymentModel]):
    entity = "CryptoPayment"

    def __init__(self, repo: CryptoPaymentRepository) -> None:
        """Bind the request's payment repository."""
        self.repo = repo

    async def create(self, data: CryptoPaymentModel) -> CryptoPaymentModel:
        """Persist a prepared payment in the caller's transaction.

        Args:
            data: Prepared payment record.

        Returns:
            The saved record with its generated identity.
        """
        payment = await self.repo.create(data)
        return payment

    async def get_by_id(self, id: int) -> CryptoPaymentModel:
        """Return the stored payment or report that it does not exist."""
        payment = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, payment)

    async def set_quote(
        self, id: int, data: Quote
    ) -> CryptoPaymentModel | None:
        """Save an unset quote in the caller's transaction."""
        payment = await self.repo.set_quote(id, data)
        return payment
