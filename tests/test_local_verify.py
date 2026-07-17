from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from tools.local_verify import (
    build_verification_steps,
    resolve_uv_run_prefix,
    run_verification_steps,
)


def test_local_verify_builds_the_expected_command_list() -> None:
    steps = build_verification_steps(("uv", "run"))

    assert [step.name for step in steps] == [
        "Pytest",
        "Ruff",
        "Black",
        "Mypy",
        "Alembic validation",
        "Repository security baseline",
        "Release readiness",
        "Operations readiness",
    ]
    assert steps[0].command == ("uv", "run", "pytest")
    assert steps[1].command == ("uv", "run", "ruff", "check", ".")
    assert steps[-1].command == (
        "uv",
        "run",
        "python",
        "tools/check_operations_readiness.py",
    )


def test_local_verify_supports_uv_direct_mode() -> None:
    uv_run_prefix = resolve_uv_run_prefix(
        python_executable=sys.executable,
        command_lookup=lambda command_name: "C:/tools/uv.exe" if command_name == "uv" else None,
    )

    assert uv_run_prefix == ("uv", "run")


def test_local_verify_supports_python_module_uv_fallback_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("UV", raising=False)

    def runner(
        command: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        assert command in (
            [sys.executable, "-m", "uv", "--version"],
            ["python", "-m", "uv", "--version"],
        )
        return subprocess.CompletedProcess(command, returncode=0)

    uv_run_prefix = resolve_uv_run_prefix(
        python_executable=sys.executable,
        repository_root=tmp_path,
        command_lookup=lambda command_name: None,
        runner=runner,
    )

    assert uv_run_prefix in (
        (sys.executable, "-m", "uv", "run"),
        ("python", "-m", "uv", "run"),
    )


def test_local_verify_exits_non_zero_when_a_required_command_fails(tmp_path: Path) -> None:
    executed_commands: list[tuple[str, ...]] = []

    def runner(
        command: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        executed_commands.append(tuple(command))
        returncode = 1 if command[-1] == "pytest" else 0
        return subprocess.CompletedProcess(command, returncode=returncode)

    exit_code = run_verification_steps(
        build_verification_steps(("uv", "run")),
        repository_root=tmp_path,
        runner=runner,
    )

    assert exit_code == 1
    assert executed_commands == [("uv", "run", "pytest")]
