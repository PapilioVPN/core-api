"""Administrator-owned claims inside a verified access-token payload."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType

from src.apps.core.roles.domain.types.records import PermissionsType


class AdminClaims(BaseDTO):
    role_id: IdType
    scopes: dict[str, PermissionsType]
