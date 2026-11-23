"""Bind audit operations to the shared request PostgreSQL UoW."""

from dishka import Provider, Scope, alias, provide

from src.apps.core.audit.app.interfaces.records import IAuditWriter
from src.apps.core.audit.app.queries.search import AuditQuery
from src.apps.core.audit.app.services.records import AuditService
from src.apps.core.audit.infra.pg.readers.search import AuditReader
from src.apps.core.audit.infra.pg.repositories.records import AuditRepository


class AuditProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(AuditRepository)
    service = provide(AuditService)
    writer = alias(AuditService, provides=IAuditWriter)
    reader = provide(AuditReader)
    query = provide(AuditQuery)
