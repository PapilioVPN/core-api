"""Instance IDs shared by Node's OpenVPN and Hysteria contracts."""

from typing import Annotated

from pydantic import StringConstraints

type NodeInstanceID = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
]
