"""Read persisted start outcomes for the specified instance."""

from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now

from ...domain.enums.start import XrayExecutionAction
from ...domain.models.start import XrayStartModel
from ..interfaces.start import IXrayStartRepository


class XrayStartQuery(IDChecks[XrayStartModel]):
    entity = "Xray start operation"

    def __init__(self, repo: IXrayStartRepository) -> None:
        self.repo = repo

    async def get(
        self,
        node_id: int,
        instance_id: str,
        id: int,
        *,
        revision_id: int | None = None,
        action: XrayExecutionAction = XrayExecutionAction.START,
    ) -> XrayStartModel:
        """Read this instance's operation, including an expired dispatch.

        Args:
            node_id: Owning node registry identity.
            instance_id: Native instance identity.
            id: Panel's operation tracking identity.
            revision_id: Owning revision, or None for a local-source start.
            action: Lifecycle action owned by the requested resource.

        Returns:
            The operation as observed at read time.

        Raises:
            NotFoundException: The operation is absent under this target.
        """
        stored = await self.repo.find_operation(
            node_id, instance_id, id, revision_id=revision_id, action=action
        )
        record = self._check_for_id_existence(id, stored)
        return record.observed_at(utc_now())
