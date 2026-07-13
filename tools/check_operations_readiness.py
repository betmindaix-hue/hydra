from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OPERATIONS_DOCUMENTS = (
    "docs/operations/Operations Overview.md",
    "docs/operations/Startup Runbook.md",
    "docs/operations/Shutdown Runbook.md",
    "docs/operations/Migration Runbook.md",
    "docs/operations/Rollback Runbook.md",
    "docs/operations/Recovery Runbook.md",
    "docs/operations/CI Failure Triage.md",
    "docs/operations/Local Developer Operations.md",
    "docs/operations/Environment Promotion.md",
    "docs/operations/Operational Readiness Checklist.md",
    "docs/operations/Runtime Diagnostics Contract.md",
)
REQUIRED_ANCHORS_BY_DOCUMENT = {
    "docs/operations/Operations Overview.md": (
        "/live",
        "/ready",
        "/health",
        "no live trading",
        "no exchange execution",
    ),
    "docs/operations/Startup Runbook.md": (
        "/live",
        "/ready",
        "/health",
        "uv run pytest",
    ),
    "docs/operations/Migration Runbook.md": ("uv run python tools/validate_alembic.py",),
    "docs/operations/Local Developer Operations.md": (
        "uv run pytest",
        "uv run python tools/check_repository_security.py",
        "uv run python tools/check_release_readiness.py",
    ),
}


def assert_required_operations_paths_exist(repository_root: Path = REPOSITORY_ROOT) -> None:
    missing_paths = [
        relative_path
        for relative_path in OPERATIONS_DOCUMENTS
        if not (repository_root / relative_path).exists()
    ]
    if missing_paths:
        raise AssertionError(f"Missing operations readiness paths: {missing_paths}")


def assert_required_operations_anchors(
    repository_root: Path = REPOSITORY_ROOT,
) -> None:
    missing_anchors_by_document: dict[str, list[str]] = {}

    for relative_path, anchors in REQUIRED_ANCHORS_BY_DOCUMENT.items():
        contents = (repository_root / relative_path).read_text(encoding="utf-8")
        missing_anchors = [anchor for anchor in anchors if anchor not in contents]
        if missing_anchors:
            missing_anchors_by_document[relative_path] = missing_anchors

    if missing_anchors_by_document:
        raise AssertionError(f"Missing operations readiness anchors: {missing_anchors_by_document}")


def main() -> None:
    assert_required_operations_paths_exist()
    assert_required_operations_anchors()


if __name__ == "__main__":
    main()
