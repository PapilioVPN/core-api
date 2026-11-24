"""Image formats accepted for receipt evidence."""

from enum import StrEnum


class ImageFormat(StrEnum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"

    @property
    def mime_type(self) -> str:
        return f"image/{self.value}"
