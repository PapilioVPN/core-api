"""Bind receipt persistence and reads to the request scope."""

from dishka import Provider, Scope, provide

from .infra.pg.repositories.crud import ReceiptRepository


class ReceiptProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ReceiptRepository)
