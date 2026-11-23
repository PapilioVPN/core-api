"""Catalog publication states, facets and ordering."""

from papilio.types.enums import FaStrEnum


class CatalogStatus(FaStrEnum):
    DRAFT = ("draft", "پیش‌نویس")
    PUBLISHED = ("published", "منتشرشده")
    PAUSED = ("paused", "متوقف")


class CatalogSort(FaStrEnum):
    PRIORITY = ("priority", "اولویت")
    TITLE = ("title", "عنوان")
    PRICE = ("price", "قیمت")
    CREATED_AT = ("created_at", "زمان ثبت")
