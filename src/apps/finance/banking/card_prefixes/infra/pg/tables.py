"""Native card prefix storage with one bank per unique prefix."""

from papilio.infra.db.table import BaseTable

from src.apps.finance.banking.card_prefixes.domain.models.records import (
    CardPrefixModel,
)


class CardPrefixTable(CardPrefixModel, BaseTable, table=True):
    pass
