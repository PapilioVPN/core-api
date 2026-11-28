"""Keep live routing observations and operation replies out of caches."""

from fastapi import Response


async def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
