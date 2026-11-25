"""Persist prepared pricing rates."""

from ...domain.models.records import CryptoRateModel
from ...infra.pg.repositories.crud import CryptoRateRepository


class CryptoRateService:
    def __init__(self, repo: CryptoRateRepository) -> None:
        """Bind the request's rate repository."""
        self.repo = repo

    async def save(self, data: CryptoRateModel) -> CryptoRateModel:
        """Save a prepared observation in the caller's transaction."""
        rate = await self.repo.save(data)
        return rate
