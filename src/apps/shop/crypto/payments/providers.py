"""Bind crypto payment persistence to the native request scope."""

from dishka import Provider, Scope, provide

from .infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
