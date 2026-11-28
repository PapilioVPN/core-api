"""Read a stored revision's declared inbound choices."""

from src.shared.utils.asyncio.threads import ThreadRunner

from ...domain.dtos.inbounds import project_inbounds
from ...domain.enums.inbounds import XrayRevisionInboundFailure
from ...domain.results.inbounds import XrayRevisionInbounds
from ..interfaces.records import IXrayRevisionService


class XrayRevisionInboundsQuery:
    def __init__(
        self, revisions: IXrayRevisionService, threads: ThreadRunner
    ) -> None:
        self.revisions = revisions
        self.threads = threads

    async def get(self, id: int) -> XrayRevisionInbounds:
        """Materialize one source before projecting it in a worker thread.

        Args:
            id: Stable revision ID selected by the Panel operator.

        Returns:
            The choices or a typed source or inbound-layout failure.

        Raises:
            NotFoundException: The revision does not exist.
        """
        source = await self.revisions.get_source(id)
        result: XrayRevisionInbounds
        if source is not None:
            result = await self.threads.run(
                project_inbounds, source.config_json
            )
        else:
            result = XrayRevisionInbounds(
                failure=XrayRevisionInboundFailure.SOURCE_UNAVAILABLE
            )
        return result
