from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/governance",
    "docs/templates",
    ".github/pull_request_template.md",
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    "docs/adr/ADR-0001-hexagonal-architecture.md",
)
CI_WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_CI_COMMANDS = (
    "uv run python tools/check_repository_security.py",
    "uv run python tools/check_release_readiness.py",
)


def assert_required_paths_exist(repository_root: Path = REPOSITORY_ROOT) -> None:
    missing_paths = [
        relative_path
        for relative_path in REQUIRED_PATHS
        if not (repository_root / relative_path).exists()
    ]
    if missing_paths:
        raise AssertionError(f"Missing release readiness paths: {missing_paths}")


def assert_ci_workflow_includes_release_checks(
    ci_workflow_path: Path = CI_WORKFLOW_PATH,
) -> None:
    workflow_contents = ci_workflow_path.read_text(encoding="utf-8")
    missing_commands = [
        command for command in REQUIRED_CI_COMMANDS if command not in workflow_contents
    ]
    if missing_commands:
        raise AssertionError(f"Missing CI release-readiness commands: {missing_commands}")


def main() -> None:
    assert_required_paths_exist()
    assert_ci_workflow_includes_release_checks()


if __name__ == "__main__":
    main()
