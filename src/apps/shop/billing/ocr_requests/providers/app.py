"""Bind OCR execution and its gateway to the application scope."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings, OCRConfig

from ..app.executions.records import OCRExecution
from ..app.interfaces.gateways import IOCRGateway
from ..app.interfaces.processing import IOCRPipeline
from ..app.pipelines.receipts import OCRPipeline
from ..infra.paddle.gateway import PaddleOCR


class AppProvider(Provider):
    scope = Scope.APP

    gateway = provide(PaddleOCR, provides=IOCRGateway)
    execution = provide(OCRExecution)
    pipeline = provide(OCRPipeline, provides=IOCRPipeline)

    @provide
    def config(self, settings: CoreSettings) -> OCRConfig:
        """Resolve the configured endpoint for the enabled worker."""
        config = settings.ocr
        if config is None:
            raise ValueError("Configure ocr.url to start receipt OCR")
        return config
