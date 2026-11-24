"""Protected address returned by a receipt image upload."""

from papilio.schemas.outputs import BaseOutput


class ImageOutput(BaseOutput):
    url: str
