"""Parse the result of a Zibal payment request."""

from typing import Annotated

from pydantic import BaseModel, Field, StrictInt

type TrackID = Annotated[int, Field(strict=True, gt=0)]


class LinkPayload(BaseModel):
    result: StrictInt
    trackId: TrackID | None = None
