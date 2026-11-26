"""Identities shared by Xray instance operations."""

from typing import Annotated

from pydantic import StringConstraints

type XrayInstanceID = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
]
