"""Select a saved revision without passing its source or a Node address."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import Field


class AssignXrayRevision(BaseDTO):
    revision_id: Annotated[IdType, Field(strict=True)]
