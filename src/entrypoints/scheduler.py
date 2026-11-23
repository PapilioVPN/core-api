"""Native worker and beat process entrypoints."""

from papilio.core.config import get_settings

from src.bootstrap.scheduler import create_scheduler
from src.settings.config import CoreSettings

broker, beat = create_scheduler(get_settings(CoreSettings))
