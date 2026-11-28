"""Validate API key issuance and panel paging inputs."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MStrType, PageType, PerPageType
from pydantic import AwareDatetime


class APIKeyCreate(BaseDTO):
    title: MStrType
    expires_at: AwareDatetime


class APIKeyList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
