from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from shutil import which

REQUIRED_REPOSITORY_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "docs/operations",
)
MAKE_COMMAND_CANDIDATES = ("make", "mingw32-make")
CommandLookup = Callable[[str], str | None]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: str
    message: str
    required: bool


def run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def detect_repository_root(search_paths: tuple[Path, ...] | None = None) -> Path | None:
    candidate_paths = search_paths or (Path.cwd(), Path(__file__).resolve())

    for raw_path in candidate_paths:
        current_path = raw_path.resolve()
        if current_path.is_file():
            current_path = current_path.parent

        for candidate in (current_path, *current_path.parents):
            if all(
                (candidate / relative_path).exists()
                for relative_path in ("pyproject.toml", "uv.lock")
            ):
                return candidate

    return None


def find_uv_module_command(
    *,
    python_executable: str,
    command_lookup: CommandLookup = which,
    runner: CommandRunner = run_command,
    repository_root: Path | None = None,
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


def find_available_make(command_lookup: CommandLookup = which) -> str | None:
    for command_name in MAKE_COMMAND_CANDIDATES:
        resolved_path = command_lookup(command_name)
        if resolved_path:
            return command_name
    return None


def find_inherited_uv_executable() -> str | None:
    inherited_uv = os.environ.get("UV")
    if not inherited_uv:
        return None

    inherited_uv_path = Path(inherited_uv)
    if inherited_uv_path.exists():
        return str(inherited_uv_path)

    return None


def evaluate_workstation(
    *,
    search_paths: tuple[Path, ...] | None = None,
    python_executable: str | None = None,
    python_version: tuple[int, int, int] | None = None,
    command_lookup: CommandLookup = which,
    runner: CommandRunner = run_command,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    resolved_python = python_executable or sys.executable
    resolved_version = python_version or sys.version_info[:3]

    python_path = Path(resolved_python)
    if python_path.exists():
        results.append(
            CheckResult(
                name="Python executable",
                status="PASS",
                message=f"Detected Python executable at {python_path}",
                required=True,
            )
        )
    else:
        results.append(
            CheckResult(
                name="Python executable",
                status="FAIL",
                message=f"Python executable could not be resolved: {resolved_python}",
                required=True,
            )
        )

    if resolved_version[:2] == (3, 12):
        results.append(
            CheckResult(
                name="Python version",
                status="PASS",
                message=(
                    f"Running Python {resolved_version[0]}."
                    f"{resolved_version[1]}.{resolved_version[2]}"
                ),
                required=True,
            )
        )
    else:
        results.append(
            CheckResult(
                name="Python version",
                status="WARN",
                message=(
                    f"Current interpreter reports Python {resolved_version[0]}."
                    f"{resolved_version[1]}.{resolved_version[2]}. "
                    "HYDRA requires Python 3.12; confirm a launcher or shim is "
                    "selecting the intended interpreter."
                ),
                required=True,
            )
        )

    repository_root = detect_repository_root(search_paths)
    if repository_root is None:
        results.append(
            CheckResult(
                name="Repository root",
                status="FAIL",
                message=(
                    "Could not detect the HYDRA repository root from the current "
                    "workstation context."
                ),
                required=True,
            )
        )
    else:
        results.append(
            CheckResult(
                name="Repository root",
                status="PASS",
                message=f"Detected repository root at {repository_root}",
                required=True,
            )
        )

    direct_uv_path = command_lookup("uv")
    inherited_uv_path = find_inherited_uv_executable()
    uv_module_command = find_uv_module_command(
        python_executable=resolved_python,
        command_lookup=command_lookup,
        runner=runner,
        repository_root=repository_root,
    )
    if direct_uv_path:
        results.append(
            CheckResult(
                name="uv",
                status="PASS",
                message=f"uv is available directly on PATH: {direct_uv_path}",
                required=True,
            )
        )
    elif inherited_uv_path is not None:
        results.append(
            CheckResult(
                name="uv",
                status="PASS",
                message=(
                    "uv is available through the current uv execution context: "
                    f"{inherited_uv_path}"
                ),
                required=True,
            )
        )
    elif uv_module_command is not None:
        results.append(
            CheckResult(
                name="uv",
                status="PASS",
                message=(
                    "uv is available through the fallback form: "
                    f"{' '.join(uv_module_command)} ..."
                ),
                required=True,
            )
        )
    else:
        results.append(
            CheckResult(
                name="uv",
                status="FAIL",
                message="uv is not available directly and python -m uv did not succeed.",
                required=True,
            )
        )

    git_path = command_lookup("git")
    if git_path:
        results.append(
            CheckResult(
                name="git",
                status="PASS",
                message=f"git is available on PATH: {git_path}",
                required=True,
            )
        )
    else:
        results.append(
            CheckResult(
                name="git",
                status="FAIL",
                message="git is required for HYDRA developer workflows but was not found on PATH.",
                required=True,
            )
        )

    if repository_root is not None:
        missing_paths = [
            relative_path
            for relative_path in REQUIRED_REPOSITORY_PATHS
            if not (repository_root / relative_path).exists()
        ]
        if missing_paths:
            results.append(
                CheckResult(
                    name="Repository files",
                    status="FAIL",
                    message=f"Missing required repository paths: {missing_paths}",
                    required=True,
                )
            )
        else:
            results.append(
                CheckResult(
                    name="Repository files",
                    status="PASS",
                    message="Required repository files and docs/operations are present.",
                    required=True,
                )
            )

    docker_path = command_lookup("docker")
    if docker_path:
        results.append(
            CheckResult(
                name="Docker",
                status="PASS",
                message=f"Docker is available on PATH: {docker_path}",
                required=False,
            )
        )
    else:
        results.append(
            CheckResult(
                name="Docker",
                status="WARN",
                message=(
                    "Docker is optional on a developer workstation. Local image "
                    "builds may be unavailable, "
                    "and GitHub Actions remains the authoritative Docker validation path."
                ),
                required=False,
            )
        )

    make_command = find_available_make(command_lookup)
    if make_command is not None:
        results.append(
            CheckResult(
                name="make",
                status="PASS",
                message=f"Make-compatible command detected: {make_command}",
                required=False,
            )
        )
    else:
        results.append(
            CheckResult(
                name="make",
                status="WARN",
                message=(
                    "make is optional. Use python -m uv ... or python tools/... "
                    "commands directly when make is unavailable."
                ),
                required=False,
            )
        )

    return results


def calculate_exit_code(results: list[CheckResult]) -> int:
    return 1 if any(result.status == "FAIL" and result.required for result in results) else 0


def format_results(results: list[CheckResult]) -> str:
    lines = ["HYDRA developer workstation check"]
    for result in results:
        lines.append(f"[{result.status}] {result.name}: {result.message}")

    failure_count = sum(1 for result in results if result.status == "FAIL")
    warning_count = sum(1 for result in results if result.status == "WARN")
    lines.append(f"Summary: {failure_count} failures, {warning_count} warnings")
    return "\n".join(lines)


def main() -> int:
    results = evaluate_workstation()
    print(format_results(results))
    return calculate_exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
