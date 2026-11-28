"""Exact six- or eight-digit issuer prefixes."""

from typing import Annotated

from pydantic import Field

CardPrefixType = Annotated[str, Field(pattern=r"^(?:[0-9]{6}|[0-9]{8})$")]
