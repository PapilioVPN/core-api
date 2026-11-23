"""Check service readiness through its public PostgreSQL probe."""

import json
from sys import exit
from urllib.request import urlopen

from papilio.core.config import get_settings

port = get_settings().run.port
with urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as response:
    status = json.load(response)["data"]["status"]
exit(status != "ok")
