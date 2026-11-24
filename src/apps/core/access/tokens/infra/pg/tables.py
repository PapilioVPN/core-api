"""One committed consumption per issuer-owned audience and token identity."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint

from src.apps.core.access.tokens.domain.models.refresh import RefreshUseModel


class RefreshUseTable(RefreshUseModel, BaseTable, table=True):
    table_name = "tbl_identity_refresh_uses"
    __table_args__ = (
        UniqueConstraint("audience", "token_id", name="uq_refresh_use"),
    )
