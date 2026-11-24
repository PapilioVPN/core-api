"""Bounded session listing inputs."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType


class SessionList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
