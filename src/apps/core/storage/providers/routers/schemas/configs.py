"""Public S3 settings and credential-presence flags."""

from typing import Literal

from papilio.schemas.outputs import BaseOutput


class S3ConfigOutput(BaseOutput):
    bucket: str | None
    endpoint_url: str | None
    public_base_url: str | None
    region_name: str | None
    addressing_style: Literal["auto", "path", "virtual"] | None
    has_aws_access_key_id: bool
    has_aws_secret_access_key: bool
    has_aws_session_token: bool


class StorageProviderConfigOutput(BaseOutput):
    provider_id: int
    is_empty: bool
    config: S3ConfigOutput
