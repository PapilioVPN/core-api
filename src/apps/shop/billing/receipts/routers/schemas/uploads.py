"""Storage URL returned after a receipt image upload."""

from papilio.schemas.outputs import BaseOutput


class ReceiptUploadOutput(BaseOutput):
    url: str
