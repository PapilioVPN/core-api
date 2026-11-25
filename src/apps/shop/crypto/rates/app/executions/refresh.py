"""Own the short database phase after reading the rate feed."""

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from ...domain.models.records import CryptoRateModel
from ..interfaces.services import ICryptoRateService


class RateRefreshExecution:
    def __init__(self, container: AsyncContainer) -> None:
        """Bind the native application container for short write scopes."""
        self.container = container

    @request_scoped
    @transactional
    async def complete(
        self, data: CryptoRateModel, *, rates: ICryptoRateService = Inject()
    ) -> CryptoRateModel:
        """Commit the observed rate in a short native request.

        Args:
            data: Prepared rate and provenance, without network resources.
            rates: The record service injected for this write.

        Returns:
            The saved rate after the execution's transaction completes.
        """
        rate = await rates.save(data)
        return rate
