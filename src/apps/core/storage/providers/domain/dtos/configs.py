"""Complete S3 connection input; persistence keeps a separate JSON object."""

from typing import Literal

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import ContentType, ValueType
from pydantic import Field, HttpUrl


class S3Config(BaseDTO):
    """Validate connection fields without contacting the object store.

    Endpoint and region remain optional for SDK endpoint resolution. The public
    base URL is the bucket/CDN root used for new upload URLs, not SDK access.
    Explicit credentials are required; session tokens support temporary
    credentials.
    Credentials remain exact for internal use and are excluded from repr.
    """

    bucket: ValueType
    aws_access_key_id: ValueType = Field(repr=False)
    aws_secret_access_key: ValueType = Field(repr=False)
    aws_session_token: ContentType | None = Field(
        default=None, min_length=1, repr=False
    )
    endpoint_url: HttpUrl | None = None
    public_base_url: HttpUrl | None = None
    region_name: ValueType | None = None
    addressing_style: Literal["auto", "path", "virtual"] = "auto"
