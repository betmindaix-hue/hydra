from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from tools.check_developer_workstation import (
    calculate_exit_code,
    evaluate_workstation,
)


def create_repository_layout(repository_root: Path) -> None:
    (repository_root / "pyproject.toml").write_text("[project]\nname='hydra'\n", encoding="utf-8")
    (repository_root / "uv.lock").write_text("# lockfile\n", encoding="utf-8")
    (repository_root / "docs" / "operations").mkdir(parents=True)


def test_workstation_check_passes_when_required_commands_and_files_are_detected(
    tmp_path: Path,
) -> None:
    create_repository_layout(tmp_path)

    def command_lookup(command_name: str) -> str | None:
        mapping = {
            "uv": "C:/tools/uv.exe",
            "git": "C:/tools/git.exe",
            "docker": "C:/tools/docker.exe",
            "make": "C:/tools/make.exe",
        }
        return mapping.get(command_name)

    results = evaluate_workstation(
        search_paths=(tmp_path,),
        python_executable=sys.executable,
        python_version=(3, 12, 0),
        command_lookup=command_lookup,
    )

    assert calculate_exit_code(results) == 0
    assert all(result.status == "PASS" for result in results)


def test_workstation_check_warns_but_does_not_fail_when_optional_docker_is_missing(
    tmp_path: Path,
) -> None:
    create_repository_layout(tmp_path)

    def command_lookup(command_name: str) -> str | None:
        mapping = {
            "uv": "C:/tools/uv.exe",
            "git": "C:/tools/git.exe",
            "make": "C:/tools/make.exe",
        }
        return mapping.get(command_name)

    results = evaluate_workstation(
        search_paths=(tmp_path,),
        python_executable=sys.executable,
        python_version=(3, 12, 0),
        command_lookup=command_lookup,
    )

    assert calculate_exit_code(results) == 0
    docker_result = next(result for result in results if result.name == "Docker")
    assert docker_result.status == "WARN"


def test_workstation_check_warns_but_does_not_fail_when_optional_make_is_missing(
    tmp_path: Path,
) -> None:
    create_repository_layout(tmp_path)

    def command_lookup(command_name: str) -> str | None:
        mapping = {
            "uv": "C:/tools/uv.exe",
            "git": "C:/tools/git.exe",
            "docker": "C:/tools/docker.exe",
        }
        return mapping.get(command_name)

    results = evaluate_workstation(
        search_paths=(tmp_path,),
        python_executable=sys.executable,
        python_version=(3, 12, 0),
        command_lookup=command_lookup,
    )

    assert calculate_exit_code(results) == 0
    make_result = next(result for result in results if result.name == "make")
    assert make_result.status == "WARN"


def test_workstation_check_fails_when_uv_fallback_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_repository_layout(tmp_path)
    monkeypatch.delenv("UV", raising=False)

    def command_lookup(command_name: str) -> str | None:
        mapping = {
            "git": "C:/tools/git.exe",
            "docker": "C:/tools/docker.exe",
            "make": "C:/tools/make.exe",
        }
        return mapping.get(command_name)

    def runner(
        command: list[str],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, returncode=1)

    results = evaluate_workstation(
        search_paths=(tmp_path,),
        python_executable=sys.executable,
        python_version=(3, 12, 0),
        command_lookup=command_lookup,
        runner=runner,
    )

    assert calculate_exit_code(results) == 1
    uv_result = next(result for result in results if result.name == "uv")
    assert uv_result.status == "FAIL"
