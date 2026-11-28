"""Validate the document shape without changing its source bytes."""

from pydantic_core import PydanticCustomError, from_json


def require_json_object(source: bytes) -> bytes:
    """Require strict JSON with an object at its root."""
    try:
        parsed = from_json(source, allow_inf_nan=False)
    except ValueError:
        raise PydanticCustomError(
            "xray_revision_json", "Enter a valid JSON object"
        ) from None
    if not isinstance(parsed, dict):
        raise PydanticCustomError(
            "xray_revision_json", "Enter a valid JSON object"
        )
    return source
