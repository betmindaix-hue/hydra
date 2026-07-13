from __future__ import annotations

from pathlib import Path

import pytest
from tools.check_operations_readiness import (
    OPERATIONS_DOCUMENTS,
    REQUIRED_ANCHORS_BY_DOCUMENT,
    assert_required_operations_anchors,
    assert_required_operations_paths_exist,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_operations_readiness_checks_pass_for_repository() -> None:
    assert_required_operations_paths_exist(REPOSITORY_ROOT)
    assert_required_operations_anchors(REPOSITORY_ROOT)


def test_operations_readiness_fails_when_required_paths_are_missing(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="Missing operations readiness paths"):
        assert_required_operations_paths_exist(tmp_path)


def test_operations_readiness_fails_when_required_operational_anchor_is_missing(
    tmp_path: Path,
) -> None:
    for relative_path in OPERATIONS_DOCUMENTS:
        target_path = tmp_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("placeholder operations document\n", encoding="utf-8")

    for relative_path, anchors in REQUIRED_ANCHORS_BY_DOCUMENT.items():
        target_path = tmp_path / relative_path
        target_path.write_text("\n".join(anchors), encoding="utf-8")

    target_path = tmp_path / "docs/operations/Startup Runbook.md"
    target_path.write_text("/live\n/ready\n/health\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="Startup Runbook.md"):
        assert_required_operations_anchors(tmp_path)
