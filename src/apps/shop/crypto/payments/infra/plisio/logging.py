"""Keep the Plisio query-string key out of HTTPX request logs."""

from logging import Filter, LogRecord

from httpx import URL


class RedactAPIKey(Filter):
    def filter(self, record: LogRecord) -> bool:
        """Remove credentials from structured Plisio URLs before logging."""
        args = record.args
        if isinstance(args, tuple):
            record.args = tuple(
                arg.copy_remove_param("api_key")
                if isinstance(arg, URL) and arg.host == "api.plisio.net"
                else arg
                for arg in args
            )
        return True
