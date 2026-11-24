"""Read text lines through the PaddleOCR 3.6 serving contract."""

from base64 import b64encode
from typing import Annotated, Literal

from httpx import HTTPError
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway
from pydantic import BaseModel, Field

from src.settings.config import OCRConfig

from ...domain.errors import OCRFailure


class Lines(BaseModel):
    rec_texts: tuple[str, ...]
    rec_scores: tuple[Annotated[float, Field(ge=0, le=1)], ...]


class Page(BaseModel):
    pruned_result: Lines = Field(alias="prunedResult")


class Result(BaseModel):
    pages: tuple[Page, ...] = Field(alias="ocrResults", max_length=1)


class Response(BaseModel):
    error_code: Literal[0] = Field(alias="errorCode")
    result: Result


class PaddleOCR(BaseGateway):
    def __init__(self, connection: HTTPConnection, config: OCRConfig) -> None:
        """Bind the reusable HTTP pool and the exact operator-owned URL."""
        super().__init__(connection, timeout=config.timeout)
        self.url = str(config.url)
        self.min_score = config.min_score

    async def read(self, image: bytes) -> tuple[str, ...]:
        """Return text lines that meet the configured threshold.

        Args:
            image: Original image bytes bounded by the calling pipeline.

        Returns:
            Recognized text lines from the configured PaddleOCR service.

        Raises:
            OCRFailure: The network request or response validation fails.
        """
        lines: list[str] = []
        try:
            response = await self.post(
                self.url,
                json={
                    "file": b64encode(image).decode("ascii"),
                    "fileType": 1,
                    "visualize": False,
                    "textRecScoreThresh": self.min_score,
                },
            )
            response.raise_for_status()
            result = Response.model_validate_json(response.content).result
            for page in result.pages:
                data = page.pruned_result
                lines.extend(
                    line
                    for line, score in zip(
                        data.rec_texts, data.rec_scores, strict=True
                    )
                    if score >= self.min_score
                )
        except HTTPError as error:
            raise OCRFailure("ocr_api_unavailable") from error
        except ValueError as error:
            raise OCRFailure("ocr_response_invalid") from error
        return tuple(lines)
