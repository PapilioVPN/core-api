"""Persist payment records and their manual review outcome."""

from collections.abc import Sequence

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import PaymentReview
from ...domain.models.records import PaymentModel
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentCRUD(IDChecks[PaymentModel]):
    entity = "Payment"

    def __init__(self, repo: PaymentRepository) -> None:
        """Bind this request's payment repository.

        Args:
            repo: Native PostgreSQL payment repository.

        Returns:
            None.
        """
        self.repo = repo

    @transactional
    async def create(self, data: PaymentModel) -> PaymentModel:
        """Persist a prepared payment.

        Args:
            data: Pending payment with verified customer and destination IDs.

        Returns:
            The stored payment.
        """
        payment = await self.repo.create(data)
        return payment

    async def get_by_id(self, id: int) -> PaymentModel:
        """Read one customer payment.

        Args:
            id: Stored payment identity.

        Returns:
            The payment and any recorded review.

        Raises:
            NotFoundException: The payment is absent.
        """
        payment = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, payment)

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[PaymentModel]:
        """Read known payment IDs in one native selection.

        Args:
            ids: Bounded set of payment identities.

        Returns:
            Unique payment matches, omitting missing identities.
        """
        payments = await self.repo.get_by_ids(ids) if ids else []
        return payments

    @transactional
    async def review(
        self, id: int, data: PaymentReview, *, reviewer_id: int
    ) -> PaymentModel:
        """Confirm or reject a pending transfer once.

        Args:
            id: Stored payment identity.
            data: Validated review outcome.
            reviewer_id: Identity of the authorized reviewer.

        Returns:
            The updated payment with the reviewer and decision time.

        Raises:
            NotFoundException: The payment is absent.
            ConflictException: A review already decided the payment.
        """
        payment = await self.repo.review(
            id, data.status, reviewer_id=reviewer_id
        )
        if payment is None:
            await self.get_by_id(id)
            raise ConflictException(
                message="This payment has already been reviewed.",
                message_code="payment_reviewed",
                unique_dict={"id": id},
            )
        return payment
