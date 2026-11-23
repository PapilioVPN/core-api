"""Storage for configured customer groups."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from ...domain.models.records import CustomerGroupModel


class CustomerGroupTable(CustomerGroupModel, BaseTable, table=True):
    __table_args__ = (Index("ix_customer_groups_priority", "priority", "id"),)
