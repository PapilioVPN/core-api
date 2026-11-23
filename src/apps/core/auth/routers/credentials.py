"""Preserve native validation errors without echoing credential inputs."""

from collections.abc import Callable, Coroutine
from typing import Any

from dishka.integrations.fastapi import DishkaRoute
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError


class CredentialRoute(DishkaRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                response = await handler(request)
            except RequestValidationError as error:
                errors = [
                    {
                        key: value
                        for key, value in item.items()
                        if key in {"type", "loc", "msg"}
                    }
                    for item in error.errors()
                ]
                raise RequestValidationError(errors) from None
            return response

        return handle
