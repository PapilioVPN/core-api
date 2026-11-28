"""Register and review card payments."""

from datetime import datetime

from papilio.errors.exceptions import ConflictException, ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.dtos.records import CardPaymentCreate
from ...domain.dtos.review import CardPaymentReview
from ...domain.enums.records import PaymentMode, PaymentStatus
from ...domain.models.records import CardPaymentModel
from ...infra.pg.repositories.crud import CardPaymentRepository


class CardPaymentService(IDChecks[CardPaymentModel]):
    entity = "CardPayment"

    def __init__(self, repo: CardPaymentRepository) -> None:
        self.repo = repo

    @transactional
    async def create(self, data: CardPaymentCreate) -> CardPaymentModel:
        """Store a pending payment and its receipt address together.

        Args:
            data: Selected card, validated rial amount, receipt and note.

        Returns:
            The stored pending payment with its assigned identity.
        """
        payment = await self.repo.create(
            CardPaymentModel(
                card_id=data.card_id,
                amount=data.amount,
                receipt_url=data.receipt_url,
                description=data.description,
            )
        )
        return payment

    @transactional
    async def create_auto(
        self,
        *,
        card_id: int,
        amount: int,
        payable_amount: int,
        code: str,
        expires_at: datetime,
    ) -> CardPaymentModel:
        """Store prepared automatic payment terms without a receipt.

        Args:
            card_id: Selected destination card identity.
            amount: Original amount in whole rials.
            payable_amount: Exact transfer amount in whole rials.
            code: Assigned identifier, including any leading zeroes.
            expires_at: Prepared timezone-aware expiry instant.

        Returns:
            The stored pending automatic payment.

        Raises:
            ConflictException: The amount overlaps an existing reservation.
        """
        payment = await self.repo.reserve(
            CardPaymentModel(
                card_id=card_id,
                amount=amount,
                mode=PaymentMode.AUTO,
                payable_amount=payable_amount,
                code=code,
                expires_at=expires_at,
            )
        )
        if payment is None:
            raise ConflictException(
                message="The transfer amount is already reserved.",
                message_code="card_amount_reserved",
                unique_dict={"payable_amount": payable_amount},
            )
        return payment

    async def reserved_amounts(
        self, *, first: int, last: int, expires_at: datetime
    ) -> set[int]:
        """Read the exact amounts whose validity overlaps the proposed one.

        Args:
            first: Inclusive lower amount in rials.
            last: Inclusive upper amount in rials.
            expires_at: Exclusive end of the proposed validity.

        Returns:
            Reserved rial amounts within the requested bounds.
        """
        amounts = await self.repo.reserved_amounts(
            first=first, last=last, expires_at=expires_at
        )
        return amounts

    async def get_by_id(self, id: int) -> CardPaymentModel:
        """Read the payment and its receipt address.

        Args:
            id: Stored payment identity.

        Returns:
            The stored payment.

        Raises:
            NotFoundException: The payment does not exist.
        """
        payment = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, payment)

    async def confirm_auto(
        self,
        *,
        transfer_id: int,
        card_id: int,
        amount: int,
        transferred_at: datetime,
    ) -> CardPaymentModel | None:
        """Apply verified bank facts within the caller's transaction.

        Args:
            transfer_id: The stored transfer used as confirmation evidence.
            card_id: Verified destination card.
            amount: Exact bank transfer amount in whole rials.
            transferred_at: Timestamp of the bank transfer.

        Returns:
            The newly confirmed payment, or None if no row changed.
        """
        payment = await self.repo.confirm_auto(
            transfer_id=transfer_id,
            card_id=card_id,
            amount=amount,
            transferred_at=transferred_at,
            decided_at=utc_now(),
        )
        return payment

    @transactional
    async def review(
        self, id: int, data: CardPaymentReview
    ) -> CardPaymentModel:
        """Confirm or reject a pending payment once.

        Args:
            id: Stored payment identity.
            data: Final decision and optional reason for rejection.

        Returns:
            The payment with the saved decision.

        Raises:
            ValidationException: A confirmation includes a rejection reason.
            NotFoundException: The payment does not exist.
            ConflictException: A decision was already recorded.
        """
        if data.status is PaymentStatus.CONFIRMED and data.reason is not None:
            raise ValidationException(
                message="A reason is only allowed when rejecting a payment.",
                message_code="card_payment_reason_unexpected",
                loc=["reason"],
            )
        payment = await self.repo.review(
            id, data.status, decided_at=utc_now(), reason=data.reason
        )
        if payment is None:
            await self.get_by_id(id)
            raise ConflictException(
                message="The payment has already been reviewed.",
                message_code="card_payment_already_reviewed",
                unique_dict={"id": id},
            )
        return payment
