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

    async def find_by_currency(self, currency: str) -> CryptoRateModel | None:
        """Read the stored rate for a currency, or None when absent."""
        rate = await self.repo.find_by_currency(currency)
        return rate
