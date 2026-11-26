"""Read persisted start outcomes for the specified instance."""

from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.models.start import XrayStartModel
from ..interfaces.start import IXrayStartRepository


class XrayStartQuery(IDChecks[XrayStartModel]):
    entity = "Xray start operation"

    def __init__(self, repo: IXrayStartRepository) -> None:
        self.repo = repo

    async def get(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayStartModel:
        """Read this instance's operation, including an expired dispatch.

        Args:
            node_id: Owning node registry identity.
            instance_id: Native instance identity.
            id: Panel's operation tracking identity.

        Returns:
            The operation as observed at read time.

        Raises:
            NotFoundException: The operation is absent under this target.
        """
        stored = await self.repo.find_operation(node_id, instance_id, id)
        record = self._check_for_id_existence(id, stored)
        return record.observed_at(utc_now())
