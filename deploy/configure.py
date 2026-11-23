"""Generate deployment settings and credentials on first install."""

from pathlib import Path
from secrets import token_urlsafe
from sys import argv
from tempfile import NamedTemporaryFile

import yaml


def save(path: Path, content: str) -> None:
    """Publish a complete file once. The parent directory is private."""
    with NamedTemporaryFile(
        dir=path.parent, mode="w", encoding="utf-8", delete_on_close=False
    ) as file:
        file.write(content)
        file.flush()
        draft = Path(file.name)
        draft.chmod(0o644)
        try:
            path.hardlink_to(draft)
        except FileExistsError:
            pass


def setup(directory: Path) -> None:
    """Keep existing config and reuse the database password on retry."""
    password = directory / "db.password"
    save(password, token_urlsafe(32))

    sample = Path("/app/config.yml.sample")
    config = yaml.safe_load(sample.read_text(encoding="utf-8"))
    config["run"].update(host="0.0.0.0", mode="prod")
    dsn = (
        "postgresql+asyncpg://papiliovpn:"
        f"{password.read_text(encoding='utf-8')}@postgres/papiliovpn"
    )
    config["db"].update(dsn=dsn, test_dsn=dsn + "_test")
    config["crypto"].update(
        encryption_key=token_urlsafe(32), password_salt=token_urlsafe(48)
    )
    config["jwt"].update(
        secret_key=token_urlsafe(48), api_secret=token_urlsafe(48)
    )
    config["redis"] = {
        "url": "redis://redis:6379/0",
        "max_connections": 16,
        "socket_timeout": 3,
        "socket_connect_timeout": 3,
        "health_check_interval": 15,
    }
    config["nats"] = {"servers": ["nats://nats:4222"]}
    save(directory / "config.yml", yaml.safe_dump(config, sort_keys=False))


if __name__ == "__main__":
    setup(Path(argv[1]))
