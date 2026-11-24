"""Bind OCR persistence to the native request scope."""

from dishka import Provider, Scope, provide

from ..infra.pg.repositories.crud import OCRRequestRepository


class RequestProvider(Provider):
    scope = Scope.REQUEST

    requests = provide(OCRRequestRepository)
