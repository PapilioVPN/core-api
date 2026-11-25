"""Keep query-string API credentials out of native outbound request logs."""

from logging import Filter, LogRecord

from httpx import URL


class RedactAPIKey(Filter):
    def filter(self, record: LogRecord) -> bool:
        """Remove API keys from structured HTTPX URL arguments."""
        args = record.args
        if isinstance(args, tuple):
            record.args = tuple(
                arg.copy_remove_param("api_key")
                if isinstance(arg, URL)
                and arg.host == "api.plisio.net"
                and "api_key" in arg.params
                else arg
                for arg in args
            )
        return True
