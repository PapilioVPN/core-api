"""Validate incoming rial amounts, bank timestamps, and panel filters."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType, RialType
from pydantic import AwareDatetime, Field

from src.apps.shop.banking.payment_cards.domain.types.records import (
    CardNumberType,
)

from ..enums.records import TransferSource

Amount = Annotated[RialType, Field(gt=0)]


class TransferCreate(BaseDTO):
    amount: Annotated[Amount, Field(strict=True)]
    transferred_at: AwareDatetime | None = None


class AdminTransferCreate(TransferCreate):
    card_id: Annotated[IdType, Field(strict=True)]


class HookTransferCreate(TransferCreate):
    card_number: CardNumberType | None = Field(default=None, repr=False)


class TransferList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    amount: Amount | None = None
    source: TransferSource | None = None
    card_id: IdType | None = None
