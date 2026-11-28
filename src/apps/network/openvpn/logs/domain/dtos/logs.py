"""Resume an OpenVPN feed within the execution that issued the cursor."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import UBigIntType
from pydantic import model_validator


class OpenVPNLogInput(BaseDTO):
    execution_id: str | None = None
    after_sequence: UBigIntType = 0

    @model_validator(mode="after")
    def validate_cursor(self) -> Self:
        if self.after_sequence and not self.execution_id:
            raise ValueError("execution_id is required with after_sequence")
        return self
