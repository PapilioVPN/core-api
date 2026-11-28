"""Store a payment and its observed provider link outcome."""

from papilio.tools.checks import IDChecks

from ...domain.models.records import PaymentModel
from ...domain.results.link import ProviderLink
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentService(IDChecks[PaymentModel]):
    entity = "IPGPayment"

    def __init__(self, repo: PaymentRepository) -> None:
        self.repo = repo

    async def create(self, data: PaymentModel) -> PaymentModel:
        """Store prepared payment terms under the invoking transaction.

        Args:
            data: Payment with an active gateway identity and whole rials.

        Returns:
            The stored payment with its assigned identity.
        """
        payment = await self.repo.create(data)
        return payment

    async def save_link(self, id: int, link: ProviderLink) -> PaymentModel:
        """Record the response for a payment with an open issuance attempt.

        Args:
            id: Payment identity.
            link: Provider response normalized to the local contract.

        Returns:
            The updated payment.

        Raises:
            NotFoundException: The payment or its open attempt is absent.
        """
        payment = await self.repo.save_link(id, link)
        payment = self._check_for_id_existence(id, payment)
        return payment
