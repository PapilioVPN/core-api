"""Bind OCR persistence to the native request scope."""

from dishka import Provider, Scope, provide

from ..app.interfaces.services import IOCRRequestService
from ..app.services.crud import OCRRequestService
from ..infra.pg.repositories.crud import OCRRequestRepository


class RequestProvider(Provider):
    scope = Scope.REQUEST

    requests = provide(OCRRequestRepository)
    service = provide(OCRRequestService, provides=IOCRRequestService)
