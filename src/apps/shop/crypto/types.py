"""Value types shared by crypto gateway settings and payment quotes."""

from typing import Annotated

from pydantic import Field

CurrencyCode = Annotated[
    str, Field(max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
]
