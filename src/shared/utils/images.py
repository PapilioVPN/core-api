"""Inspect image content with native Pillow decoding."""

import warnings
from pathlib import Path

from PIL import Image


def mime_checker(path: Path, mime_type: str) -> bool:
    """Check an image's actual MIME and decoding without changing its bytes.

    Args:
        path: Local image file to inspect.
        mime_type: Expected MIME from Pillow's supported image formats.

    Returns:
        Whether the image matches the MIME and decodes within Pillow's limit.
        Corrupt bytes and Pillow decompression-bomb warnings/errors reject.

    Raises:
        OSError: Opening the source file itself fails.
    """
    valid = True
    with path.open("rb") as source:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(source) as image:
                    valid = Image.MIME.get(image.format or "") == mime_type
                    if valid:
                        image.load()
        except (
            OSError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            valid = False
    return valid
