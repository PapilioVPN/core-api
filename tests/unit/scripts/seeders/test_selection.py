"""Command-line selection follows the explicit seed dependency order."""

import sys
from pathlib import Path

import pytest

from scripts.seeders.run import main

pytestmark = pytest.mark.unit


def test_list_resolves_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PAPILIO_CONFIG", str(tmp_path / "missing.yml"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["seed", "--list", "catalog.bindings", "catalog.categories"],
    )

    main()

    assert capsys.readouterr().out.splitlines() == [
        "catalog.categories (requires: none)",
        "catalog.attributes (requires: none)",
        "catalog.bindings (requires: catalog.categories, catalog.attributes)",
    ]


def test_unknown_target_fails_before_loading_configuration(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PAPILIO_CONFIG", str(tmp_path / "missing.yml"))
    monkeypatch.setattr(sys, "argv", ["seed", "catalog.missing"])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 2
    assert "Unknown seed target: catalog.missing" in capsys.readouterr().err
