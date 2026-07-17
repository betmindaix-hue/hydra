from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory

CommandLookup = Callable[[str], str | None]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True, slots=True)
class VerificationStep:
    name: str
    command: tuple[str, ...]


QUALITY_COMMANDS = (
    ("Pytest", ("pytest",)),
    ("Ruff", ("ruff", "check", ".")),
    ("Black", ("black", "--check", ".")),
    ("Mypy", ("mypy", "src", "tests", "tools")),
    ("Alembic validation", ("python", "tools/validate_alembic.py")),
    ("Repository security baseline", ("python", "tools/check_repository_security.py")),
    ("Release readiness", ("python", "tools/check_release_readiness.py")),
    ("Operations readiness", ("python", "tools/check_operations_readiness.py")),
)


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, text=True, env=env)


def detect_repository_root(search_paths: tuple[Path, ...] | None = None) -> Path | None:
    candidate_paths = search_paths or (Path.cwd(), Path(__file__).resolve())

    for raw_path in candidate_paths:
        current_path = raw_path.resolve()
        if current_path.is_file():
            current_path = current_path.parent

        for candidate in (current_path, *current_path.parents):
            if (candidate / "pyproject.toml").exists() and (candidate / "uv.lock").exists():
                return candidate

    return None


def find_uv_module_command(
    *,
    python_executable: str,
    repository_root: Path | None,
    command_lookup: CommandLookup = which,
    runner: CommandRunner = run_command,
) -> tuple[str, ...] | None:
    launcher_candidates: list[tuple[str, ...]] = [(python_executable, "-m", "uv")]

    if command_lookup("python"):
        launcher_candidates.append(("python", "-m", "uv"))

    if command_lookup("py"):
        launcher_candidates.append(("py", "-m", "uv"))

    seen_candidates: set[tuple[str, ...]] = set()
    for launcher_command in launcher_candidates:
        if launcher_command in seen_candidates:
            continue
        seen_candidates.add(launcher_command)

        completed = runner([*launcher_command, "--version"], cwd=repository_root)
        if completed.returncode == 0:
            return launcher_command

    return None


def find_inherited_uv_executable() -> str | None:
    inherited_uv = os.environ.get("UV")
    if not inherited_uv:
        return None

    inherited_uv_path = Path(inherited_uv)
    if inherited_uv_path.exists():
        return str(inherited_uv_path)

    return None


def resolve_uv_run_prefix(
    *,
    python_executable: str | None = None,
    repository_root: Path | None = None,
    command_lookup: CommandLookup = which,
    runner: CommandRunner = run_command,
) -> tuple[str, ...]:
    if command_lookup("uv"):
        return ("uv", "run")

    inherited_uv_path = find_inherited_uv_executable()
    if inherited_uv_path is not None:
        return (inherited_uv_path, "run")

    resolved_python = python_executable or sys.executable
    uv_module_command = find_uv_module_command(
        python_executable=resolved_python,
        repository_root=repository_root,
        command_lookup=command_lookup,
        runner=runner,
    )
    if uv_module_command is not None:
        return (*uv_module_command, "run")

    raise RuntimeError("uv is not available directly and python -m uv did not succeed.")


def build_verification_steps(uv_run_prefix: tuple[str, ...]) -> list[VerificationStep]:
    return [
        VerificationStep(name=name, command=uv_run_prefix + command)
        for name, command in QUALITY_COMMANDS
    ]


def run_verification_steps(
    steps: list[VerificationStep],
    *,
    repository_root: Path,
    runner: CommandRunner = run_command,
) -> int:
    with TemporaryDirectory(prefix="hydra-local-verify-") as temp_directory:
        command_environment = os.environ.copy()
        command_environment["COVERAGE_FILE"] = str(Path(temp_directory) / ".coverage")

        for step in steps:
            command_as_text = " ".join(step.command)
            print(f"[RUN] {step.name}: {command_as_text}")
            completed = runner(
                list(step.command),
                cwd=repository_root,
                env=command_environment,
            )
            if completed.returncode == 0:
                print(f"[PASS] {step.name}")
                continue

            print(f"[FAIL] {step.name}: exited with code {completed.returncode}")
            return completed.returncode or 1

    print("[PASS] Local verification completed successfully.")
    return 0


def main() -> int:
    repository_root = detect_repository_root()
    if repository_root is None:
        print("[FAIL] Could not detect the HYDRA repository root.")
        return 1

    try:
        uv_run_prefix = resolve_uv_run_prefix(repository_root=repository_root)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 1

    steps = build_verification_steps(uv_run_prefix)
    return run_verification_steps(steps, repository_root=repository_root)


if __name__ == "__main__":
    raise SystemExit(main())
