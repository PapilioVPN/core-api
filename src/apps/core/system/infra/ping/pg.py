from typing import ClassVar

from asyncpg.exceptions import (
    CannotConnectNowError,
    InvalidAuthorizationSpecificationError,
    PostgresConnectionError,
    TooManyConnectionsError,
)
from papilio.infra.db.connection import DBConnection
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import DateTime, String, func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from src.apps.core.system.domain.results.pg import PostgresServerTime


class PostgresPing:
    connection_errors: ClassVar[tuple[type[Exception], ...]] = (
        OSError,
        PostgresConnectionError,
        InvalidAuthorizationSpecificationError,
        CannotConnectNowError,
        TooManyConnectionsError,
        PoolTimeoutError,
    )

    def __init__(self, database: DBConnection[PGUnitOfWork]) -> None:
        """Bind the application-owned native database connection.

        Args:
            database: Connection used to open a separate native read UoW.

        Returns:
            None.
        """
        self.database = database

    async def ping(self) -> bool:
        """Execute SELECT 1 through a native PostgreSQL unit of work.

        Args:
            None.

        Returns:
            True when the query returns 1; False for an unavailable connection.
            Unexpected query errors and cancellation propagate unchanged.
        """
        try:
            async with self.database.uow() as unit:
                stmt = select(1)
                result = await unit.execute(stmt)
                available = result.scalar_one() == 1
        except self.connection_errors:
            available = False
        except DBAPIError as error:
            if not error.connection_invalidated:
                raise
            available = False
        return available

    async def read_server_time(self) -> PostgresServerTime | None:
        """Read the current PG clock and session timezone in one query.

        Args:
            None.

        Returns:
            Clock snapshot, or None when the connection is unavailable.
            Unexpected query errors and cancellation propagate unchanged.
        """
        try:
            async with self.database.uow() as unit:
                stmt = select(
                    func.clock_timestamp(type_=DateTime(timezone=True)),
                    func.current_setting("TimeZone", type_=String()),
                )
                result = await unit.execute(stmt)
                server_time, server_timezone = result.one()
                snapshot = PostgresServerTime(
                    server_time=server_time, server_timezone=server_timezone
                )
        except self.connection_errors:
            snapshot = None
        except DBAPIError as error:
            if not error.connection_invalidated:
                raise
            snapshot = None
        return snapshot
