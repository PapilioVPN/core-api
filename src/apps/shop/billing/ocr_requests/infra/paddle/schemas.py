"""Wire types for the PaddleOCR image endpoint."""

from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field


class ReadRequest(TypedDict):
    file: str
    fileType: Literal[1]
    visualize: Literal[False]
    textRecScoreThresh: float


class Lines(BaseModel):
    rec_texts: tuple[str, ...]
    rec_scores: tuple[Annotated[float, Field(ge=0, le=1)], ...]


class Page(BaseModel):
    pruned_result: Lines = Field(alias="prunedResult")


class Result(BaseModel):
    pages: tuple[Page, ...] = Field(alias="ocrResults", max_length=1)


class ReadResponse(BaseModel):
    error_code: Literal[0] = Field(alias="errorCode")
    result: Result
