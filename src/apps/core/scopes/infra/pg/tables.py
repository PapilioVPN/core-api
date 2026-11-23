"""Scopes table owned by access management."""

from papilio.infra.db.table import BaseTable

from src.apps.core.scopes.domain.models.records import ScopeModel


class ScopeTable(ScopeModel, BaseTable, table=True):
    pass
