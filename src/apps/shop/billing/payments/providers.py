"""Bind payment persistence and reads to the request scope."""

from dishka import Provider, Scope, provide

from .infra.pg.repositories.crud import PaymentRepository


class PaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
