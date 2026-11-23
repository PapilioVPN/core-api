"""ASGI process entrypoint for Papilio's native runner."""

from papilio.core.config import get_settings

from src.bootstrap.api import create_api
from src.settings.config import CoreSettings

app = create_api(get_settings(CoreSettings))
