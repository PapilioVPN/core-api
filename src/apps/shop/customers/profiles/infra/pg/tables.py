"""PostgreSQL tables for retail customer identities."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from ...domain.models.records import CustomerModel


class CustomerTable(CustomerModel, BaseTable, table=True):
    __table_args__ = (Index("ix_customers_blocked", "is_blocked", "id"),)
