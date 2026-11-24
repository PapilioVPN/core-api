"""Inspect image content with native Pillow decoding."""

import warnings
from pathlib import Path

from papilio.errors.exceptions import ValidationException
from PIL import Image

from src.shared.utils.asyncio.processes import ProcessRunner


async def validate_image(
    path: Path,
    mime_type: str,
    *,
    processes: ProcessRunner,
    error: ValidationException,
) -> None:
    """Validate image bytes in a worker process.

    Args:
        path: Local file available throughout validation.
        mime_type: Expected MIME of the uploaded image.
        processes: Existing runner for decoding outside the event loop.
        error: The caller's validation error for invalid content.

    Returns:
        None after the image decodes as the expected MIME.

    Raises:
        ValidationException: The image does not decode as the expected MIME.
        OSError: The source file cannot be opened.
    """
    valid = await processes.run(mime_checker, path, mime_type)
    if not valid:
        raise error


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
