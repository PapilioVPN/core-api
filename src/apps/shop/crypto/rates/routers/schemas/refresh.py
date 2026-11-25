"""Acknowledgement of a queued rate refresh."""

from papilio.schemas.outputs import BaseOutput


class RefreshAccepted(BaseOutput):
    task_id: str
