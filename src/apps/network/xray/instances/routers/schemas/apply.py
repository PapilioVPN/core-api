"""Panel representation of revision application evidence."""

from .start import XrayStartOutput


class XrayApplyOutput(XrayStartOutput):
    revision_id: int
