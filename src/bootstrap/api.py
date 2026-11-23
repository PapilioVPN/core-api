"""Compose the Core HTTP application and its native lifespan."""

from fastapi import FastAPI
from papilio.api.application import create_app

from src.bootstrap.providers.infra import infra_providers
from src.settings.config import CoreSettings


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
        docs_url=None,
        openapi_url=None,
    )
    return app
