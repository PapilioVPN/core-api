"""Validate duration definitions and paging inputs."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IntType, PageType, PerPageType
from pydantic import Field

from src.apps.shop.durations.domain.enums.start import DurationStart


class DurationCreate(BaseDTO):
    days: Annotated[IntType, Field(gt=0, strict=True)]
    starts_on: DurationStart = DurationStart.READY


class DurationList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
