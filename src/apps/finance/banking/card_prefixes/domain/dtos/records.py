"""Card prefix creation, partial update and filtered paging inputs."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType
from pydantic_core import MISSING

from ..types.records import CardPrefixType


class CardPrefixCreate(BaseDTO):
    bank_id: IdType
    prefix: CardPrefixType
    is_active: bool = True


class CardPrefixUpdate(BaseDTO):
    bank_id: IdType | MISSING = MISSING
    prefix: CardPrefixType | MISSING = MISSING
    is_active: bool | MISSING = MISSING


class CardPrefixList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    bank_id: IdType | None = None
    is_active: bool | None = None
