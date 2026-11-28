"""Wake one persisted restart step without putting the revision on the bus."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class XrayRestartRolloutRequested(BaseDTO):
    rollout_id: IdType
    operation_id: IdType
