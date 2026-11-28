"""Sources of a selected Xray log stream."""

from enum import StrEnum


class XrayLogSource(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    UNSPECIFIED = "unspecified"
