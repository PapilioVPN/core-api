"""Read text lines through the PaddleOCR serving contract."""

from base64 import b64encode

from httpx import HTTPError
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway

from src.settings.config import OCRConfig

from ...domain.results.records import OCRFailure
from .schemas import ReadRequest, ReadResponse


class PaddleGateway(BaseGateway):
    def __init__(self, connection: HTTPConnection, config: OCRConfig) -> None:
        """Bind the shared HTTP pool to the configured PaddleOCR endpoint."""
        super().__init__(connection, timeout=config.timeout)
        self.url = str(config.url)
        self.min_score = config.min_score

    async def read(self, image: bytes) -> tuple[str, ...] | OCRFailure:
        """Read ordered text lines and blank low-confidence positions.

        Args:
            image: Original image bytes bounded by the pipeline.

        Returns:
            Trusted text in its original positions or a safe failure code.
        """
        payload: ReadRequest = {
            "file": b64encode(image).decode("ascii"),
            "fileType": 1,
            "visualize": False,
            "textRecScoreThresh": 0.0,
        }
        try:
            response = await self.post(self.url, json=payload)
            response.raise_for_status()
        except HTTPError:
            lines = OCRFailure("ocr_api_unavailable")
        else:
            try:
                result = ReadResponse.model_validate_json(
                    response.content
                ).result
                lines = tuple(
                    line if score >= self.min_score else ""
                    for page in result.pages
                    for line, score in zip(
                        page.pruned_result.rec_texts,
                        page.pruned_result.rec_scores,
                        strict=True,
                    )
                )
            except ValueError:
                lines = OCRFailure("ocr_response_invalid")
        return lines
