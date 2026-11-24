"""Bind OCR attempts, native execution and the internal API gateway."""

from dishka import Provider, Scope, provide
from papilio.core.config import Settings
from papilio.infra.http.connection import HTTPConnection

from src.settings.config import CoreSettings

from .app.executions.records import OCRExecution
from .app.interfaces.gateways import IOCRGateway
from .app.pipelines.receipts import OCRPipeline
from .infra.paddle.gateway import PaddleOCR
from .infra.pg.repositories.crud import OCRRequestRepository


class OCRProvider(Provider):
    requests = provide(OCRRequestRepository, scope=Scope.REQUEST)
    execution = provide(OCRExecution, scope=Scope.APP)
    pipeline = provide(OCRPipeline, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def gateway(
        self, connection: HTTPConnection, settings: Settings
    ) -> IOCRGateway:
        """Use the process HTTP pool for the configured PaddleOCR endpoint."""
        if not isinstance(settings, CoreSettings) or settings.ocr is None:
            raise ValueError("Configure ocr.url to start receipt OCR")
        gateway = PaddleOCR(connection, settings.ocr)
        return gateway
