"""Run the link creation command between committed SQL phases."""

from pydantic import HttpUrl

from ...domain.results.link import LinkFailure, LinkResult
from ..interfaces.link import ILinkExecution, IVarizaClient


class LinkPipeline:
    def __init__(
        self, execution: ILinkExecution, variza: IVarizaClient
    ) -> None:
        self.execution = execution
        self.variza = variza

    async def create(self, id: int, return_url: HttpUrl) -> LinkResult:
        """Issue or reuse a link for a payment already committed by the caller.

        Args:
            id: Identity of the payment holding the trusted rial amount.
            return_url: Trusted HTTPS destination after Variza redirects the
                buyer. The caller starts this operation outside its SQL work.

        Returns:
            A persisted link or the typed outcome of the attempt.
        """
        prepared = await self.execution.prepare(id)
        result = prepared.result
        if prepared.request is not None:
            result = await self.variza.create(prepared.request, return_url)
            if result.failure is not LinkFailure.UNKNOWN:
                result = await self.execution.finish(id, result)
        return result
