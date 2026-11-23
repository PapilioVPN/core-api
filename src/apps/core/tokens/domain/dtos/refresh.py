"""Validated bounds for refresh-consumption maintenance jobs."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PerPageType


class RefreshUseCleanup(BaseDTO):
    limit: PerPageType = 100
