"""Inputs for configuring and filtering payment destination cards."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, MStrType, PageType, PerPageType
from pydantic_core import MISSING

from ..types.records import CardNumberType


class CardCreate(BaseDTO):
    card_number: CardNumberType
    holder_name: MStrType
    is_active: bool = True
    allow_manual: bool = True
    allow_auto: bool = False


class CardUpdate(BaseDTO):
    card_number: CardNumberType | MISSING = MISSING
    holder_name: MStrType | MISSING = MISSING
    is_active: bool | MISSING = MISSING
    allow_manual: bool | MISSING = MISSING
    allow_auto: bool | MISSING = MISSING


class CardList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: MStrType | None = None
    bank_id: IdType | None = None
    is_active: bool | None = None
    allow_manual: bool | None = None
    allow_auto: bool | None = None
