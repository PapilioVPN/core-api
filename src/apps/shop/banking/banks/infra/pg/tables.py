"""PostgreSQL reference data owned by banks."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from ...domain.models.records import BankModel


class BankTable(BankModel, BaseTable, table=True):
    __table_args__ = (Index("ix_banks_priority", "priority", "id"),)
