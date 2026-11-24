"""Stable actions exposed in the administrator audit history."""

from papilio.types.enums import FaStrEnum


class AuditAction(FaStrEnum):
    USER_ROLE_UPDATE = ("user.role.update", "تغییر نقش حساب")
    ROLE_SCOPE_CREATE = ("role.scope.create", "تخصیص مجوز")
    ROLE_SCOPE_UPDATE = ("role.scope.update", "تغییر مجوز")
    ROLE_SCOPE_REMOVE = ("role.scope.remove", "حذف مجوز")
    SESSION_REVOKE = ("session.revoke", "بستن نشست")
    SESSION_REVOKE_OTHERS = ("session.revoke_others", "بستن نشست‌های دیگر")
