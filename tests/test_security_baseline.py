from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from tools.check_repository_security import (
    ENV_EXAMPLE_PATHS,
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


@pytest.mark.parametrize("env_example_path", ENV_EXAMPLE_PATHS)
def test_env_example_uses_placeholders_only(env_example_path: Path) -> None:
    assert_env_example_uses_placeholders(env_example_path)


def test_startup_diagnostics_do_not_emit_raw_runtime_secrets() -> None:
    settings = build_runtime_settings(
        database_url="postgresql+psycopg://hydra:supersecret@localhost:5432/hydra",
        redis_url="redis://:redis-secret@localhost:6379/0",
    )

    diagnostics = build_startup_diagnostics(
        settings,
        live_trading_enabled=False,
        architecture_mode="ddd-hexagonal",
    )

    diagnostics_payload = str(diagnostics)

    assert "database_url" not in diagnostics
    assert "redis_url" not in diagnostics
    assert "supersecret" not in diagnostics_payload
    assert "redis-secret" not in diagnostics_payload
    assert "postgresql+psycopg://hydra:supersecret@localhost:5432/hydra" not in diagnostics_payload


def test_no_forbidden_exchange_or_secret_source_keywords() -> None:
    assert_no_forbidden_source_keywords(
        (
            REPOSITORY_ROOT / "src",
            REPOSITORY_ROOT / "tools",
            REPOSITORY_ROOT / ".github",
        )
    )
