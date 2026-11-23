"""Validate the offline Iranian banking snapshot before database execution."""

from pathlib import Path

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IntType, MediaUrlType, MStrType
from pydantic import Field

from src.apps.shop.banking.banks.domain.types.records import BankCodeType
from src.apps.shop.banking.card_prefixes.domain.types.records import (
    CardPrefixType,
)

SNAPSHOT = Path(__file__).with_name("data") / "iran.json"


class BankSeed(BaseDTO):
    code: BankCodeType
    title: MStrType
    icon_url: MediaUrlType | None = None
    is_active: bool = True
    priority: IntType = 0
    prefixes: list[CardPrefixType] = Field(default_factory=list)


class BankingSeed(BaseDTO):
    banks: list[BankSeed] = Field(min_length=1)


def load_banking(path: Path = SNAPSHOT) -> BankingSeed:
    """Validate fields and unique bank/prefix identities offline.

    Args:
        path: Reviewed Iranian banking snapshot to import.

    Returns:
        Validated bank references and their exact prefix strings.

    Raises:
        ValueError: A bank code or card prefix occurs more than once.
    """
    data = BankingSeed.model_validate_json(path.read_bytes())
    codes = [bank.code for bank in data.banks]
    if len(codes) != len(set(codes)):
        raise ValueError("Bank codes must be unique")
    prefixes = [prefix for bank in data.banks for prefix in bank.prefixes]
    if len(prefixes) != len(set(prefixes)):
        raise ValueError("Card prefixes must be unique across banks")
    return data
