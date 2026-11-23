"""Value constraints for role permissions."""

from typing import Annotated

from pydantic import Field

PermissionsType = Annotated[int, Field(ge=0, le=15)]
