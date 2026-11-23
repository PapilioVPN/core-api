"""Supported feature types and PapilioVPN subscription parameter keys."""

from enum import StrEnum


class AttributeType(StrEnum):
    STR = "str"
    INT = "int"
    BOOL = "bool"


class ParamKey(StrEnum):
    DURATION_DAYS = "duration_days"
    QUOTA_BYTES = "quota_bytes"
