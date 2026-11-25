"""Persist cryptocurrency payment records."""

from ...domain.models.records import CryptoPaymentModel
from ...infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentService:
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
