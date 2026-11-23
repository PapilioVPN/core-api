"""Compose the Core HTTP application and its native lifespan."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from papilio.api.application import create_app
from papilio.api.responses.envelope import APIResponse

from src.bootstrap.providers.infra import infra_providers
from src.settings.config import CoreSettings


async def _validation_error(
    _request: Request, error: Exception
) -> JSONResponse:
    """Serialize native validation errors without rejected request values."""
    assert isinstance(error, RequestValidationError)
    response = APIResponse.from_pydantic_error(error)
    content = response.model_dump(
        mode="json",
        exclude_defaults=True,
        exclude={"errors": {"__all__": {"input", "ctx"}}},
    )
    return JSONResponse(content, status_code=422)


def create_api(settings: CoreSettings) -> FastAPI:
    """Compose native module discovery, providers and HTTP error handling.

    Args:
        settings: Validated startup settings.

    Returns:
        The ASGI application with application-owned dependency lifetimes.
    """
    app = create_app(
        settings,
        providers=infra_providers(settings),
        exception_handlers={RequestValidationError: _validation_error},
        docs_url=None,
        openapi_url=None,
    )
    return app
