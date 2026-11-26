"""Read configured providers that can issue an invoice."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.schemas.results import PagedType
from sqlalchemy import func, or_, select
from sqlmodel import col

from ....domain.results.methods import GatewayOption
from ..tables import CryptoGatewayConfigTable, CryptoGatewayTable


class GatewayMethodsReader(PGReader):
    async def list(
        self, amount: int, *, limit: int, offset: int
    ) -> PagedType[GatewayOption]:
        """Page eligible hosted gateways for the original rial amount.

        Args:
            amount: Original amount in whole rials.
            limit: Maximum options to return.
            offset: Number of matching accounts to skip.

        Returns:
            Gateway choices in ID order and their total.
        """
        gateway = CryptoGatewayTable
        config = CryptoGatewayConfigTable
        settings = col(config.config)
        currency = func.coalesce(settings["price_currency"].as_string(), "IRR")
        lower = col(gateway.min_amount)
        upper = col(gateway.max_amount)
        query = (
            select(
                col(gateway.id),
                col(gateway.kind),
                col(gateway.title),
                col(gateway.icon_url),
                lower,
                upper,
                currency,
            )
            .join(config, col(config.gateway_id) == col(gateway.id))
            .where(
                col(gateway.is_active).is_(True),
                col(gateway.kind) == "plisio",
                settings["api_key"].as_string() != "",
                currency.in_(("IRR", "USD")),
                or_(lower.is_(None), lower <= amount),
                or_(upper.is_(None), upper >= amount),
            )
        )
        stmt = select(func.count()).select_from(query.subquery())
        result = await self.uow.execute(stmt)
        total = result.scalar_one()
        items: list[GatewayOption] = []
        if offset < total:
            stmt = query.order_by(col(gateway.id)).limit(limit).offset(offset)
            rows = await self.uow.execute(stmt)
            items = [GatewayOption(*row) for row in rows.tuples()]
        return PagedType(items=items, total_items=total)
