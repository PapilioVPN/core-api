"""Native transactional Outbox relay entrypoint."""

from papilio.core.config import get_settings

from src.bootstrap.relay import create_relay_app
from src.settings.config import CoreSettings

app = create_relay_app(get_settings(CoreSettings))
