"""Read ordered rollout evidence scoped to the selected revision."""

from papilio.tools.checks import IDChecks

from ...domain.results.rollout import RestartRolloutSnapshot
from ..interfaces.rollout import IRestartRolloutReader


class RestartRolloutQuery(IDChecks[RestartRolloutSnapshot]):
    entity = "Xray restart rollout"

    def __init__(self, reader: IRestartRolloutReader) -> None:
        self.reader = reader

    async def get(self, revision_id: int, id: int) -> RestartRolloutSnapshot:
        snapshot = await self.reader.read(revision_id, id)
        return self._check_for_id_existence(id, snapshot)
