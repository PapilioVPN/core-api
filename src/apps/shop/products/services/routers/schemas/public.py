"""Storefront service fields exposed over HTTP."""

from papilio.schemas.outputs import BaseOutput


class PublicServiceOutput(BaseOutput):
    id: int
    title: str
    description: str | None
