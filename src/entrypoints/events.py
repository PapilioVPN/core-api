"""Native Papilio Tasks event worker entrypoint."""

from papilio.core.config import get_settings

from src.bootstrap.events import create_events
from src.settings.config import CoreSettings

app = create_events(get_settings(CoreSettings))
