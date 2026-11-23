"""Inspect receipt images using native Pillow decoding."""

from pathlib import Path

from PIL import Image

MAX_PIXELS = 16_000_000


def is_image(path: Path, mime_type: str) -> bool:
    """Check actual image content without changing the staged bytes.

    Args:
        path: Staged file borrowed from the storage operation.
        mime_type: Expected media type of the original image.

    Returns:
        Whether the file matches the MIME type and decodes within the limit.

    Raises:
        OSError: The staged file could not be opened.
    """
    with path.open("rb") as source:
        try:
            with Image.open(source, formats=["JPEG", "PNG", "WEBP"]) as image:
                if (
                    Image.MIME.get(image.format or "") != mime_type
                    or image.width * image.height > MAX_PIXELS
                ):
                    return False
                image.load()
        except (OSError, ValueError, Image.DecompressionBombError):
            return False
    return True
