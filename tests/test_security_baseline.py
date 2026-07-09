from __future__ import annotations

import subprocess
from pathlib import Path

from tools.check_repository_security import (
    assert_env_example_uses_placeholders,
    assert_no_forbidden_source_keywords,
)

from hydra.infrastructure.logging import build_startup_diagnostics
from tests.support import build_runtime_settings

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_env_file_is_gitignored() -> None:
    result = subprocess.run(
        ["git", "check-ignore", ".env"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert ".env" in result.stdout


def test_env_example_uses_placeholders_only() -> None:
    assert_env_example_uses_placeholders(REPOSITORY_ROOT / ".env.example")


def test_startup_diagnostics_do_not_emit_raw_database_url() -> None:
    settings = build_runtime_settings(
        database_url="postgresql+psycopg://hydra:supersecret@localhost:5432/hydra"
    )

    diagnostics = build_startup_diagnostics(
        settings,
        live_trading_enabled=False,
        architecture_mode="ddd-hexagonal",
    )

    diagnostics_payload = str(diagnostics)

    assert "database_url" not in diagnostics
    assert "supersecret" not in diagnostics_payload
    assert "postgresql+psycopg://hydra:supersecret@localhost:5432/hydra" not in diagnostics_payload


def test_no_forbidden_exchange_or_secret_source_keywords() -> None:
    assert_no_forbidden_source_keywords(
        (
            REPOSITORY_ROOT / "src",
            REPOSITORY_ROOT / "tools",
            REPOSITORY_ROOT / ".github",
        )
    )
