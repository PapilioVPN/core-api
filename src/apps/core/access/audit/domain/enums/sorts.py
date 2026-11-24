"""Sort options for the administrator audit history."""

from papilio.types.enums import FaStrEnum


class AuditSortBy(FaStrEnum):
    CREATED_AT = ("created_at", "زمان ثبت")
    ID = ("id", "شناسه")
