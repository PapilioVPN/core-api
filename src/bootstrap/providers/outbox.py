"""Bind native event registration to the request's PostgreSQL transaction."""

from dishka import Provider, Scope, provide
from papilio.infra.db.uow import PGUnitOfWork
from papilio_tasks.apps.outbox import Outbox, OutboxWriter

from src.bootstrap.outbox import create_outbox
from src.settings.config import CoreSettings


class OutboxProvider(Provider):
    def __init__(self, settings: CoreSettings) -> None:
        super().__init__()
        self.settings = settings

    @provide(scope=Scope.APP)
    def outbox(self) -> Outbox:
        """Build the application publication registry."""
        runtime = create_outbox(self.settings)
        return runtime

    @provide(scope=Scope.REQUEST)
    def writer(self, runtime: Outbox, unit: PGUnitOfWork) -> OutboxWriter:
        """Borrow the operation's SQL session for event registration."""
        writer = runtime.writer(unit.session)
        return writer
