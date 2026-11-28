"""Match the Linux interface identity accepted by Node."""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints


def _validate_name(value: str) -> str:
    if (
        value in {".", ".."}
        or len(value.encode("utf-8")) > 15
        or any(character in "\x00/: \t\n\v\f\r" for character in value)
    ):
        raise ValueError("Enter a valid Linux interface name")
    return value


type WireGuardInterfaceName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=15),
    AfterValidator(_validate_name),
]
