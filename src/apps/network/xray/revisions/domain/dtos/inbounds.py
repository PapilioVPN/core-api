"""Project the fields needed to select a declared Xray inbound."""

from typing import Annotated

from pydantic import BaseModel, Field, ValidationError

from ..enums.inbounds import XrayRevisionInboundFailure
from ..results.inbounds import XrayRevisionInbound


class _StreamSettings(BaseModel):
    network: str | None = None
    security: str | None = None


class _Inbound(BaseModel):
    tag: str | None = None
    protocol: Annotated[str, Field(min_length=1)]
    stream_settings: _StreamSettings | None = Field(
        default=None, validation_alias="streamSettings"
    )


class _Config(BaseModel):
    inbounds: list[_Inbound] | None = None


def project_inbounds(
    source: bytes,
) -> tuple[XrayRevisionInbound, ...] | XrayRevisionInboundFailure:
    """Return only explicitly tagged choices in source order.

    Args:
        source: Verified bytes of one saved JSON revision.

    Returns:
        The projected choices or an invalid layout or duplicate-tag failure.
    """
    try:
        config = _Config.model_validate_json(source, strict=True)
    except ValidationError:
        result = XrayRevisionInboundFailure.INVALID
    else:
        choices = tuple(
            XrayRevisionInbound(
                tag=inbound.tag,
                protocol=inbound.protocol,
                network=inbound.stream_settings.network
                if inbound.stream_settings is not None
                else None,
                security=inbound.stream_settings.security
                if inbound.stream_settings is not None
                else None,
            )
            for inbound in config.inbounds or ()
            if inbound.tag
        )
        result = (
            choices
            if len({choice.tag for choice in choices}) == len(choices)
            else XrayRevisionInboundFailure.INVALID
        )
    return result
