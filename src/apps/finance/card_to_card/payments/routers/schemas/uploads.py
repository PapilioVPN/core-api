"""Return the stored URL for a receipt image."""

from papilio.schemas.outputs import BaseOutput


class ReceiptUploadOutput(BaseOutput):
    url: str
