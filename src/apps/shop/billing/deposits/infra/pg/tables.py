"""Native discovery for persisted bank deposits."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import DepositModel


class DepositTable(DepositModel, BaseTable, table=True):
    pass
