from __future__ import annotations

from pathlib import Path

import pytest
from tools.check_release_readiness import (
    assert_ci_workflow_includes_release_checks,
    assert_required_paths_exist,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_release_readiness_checks_pass_for_repository() -> None:
    assert_required_paths_exist(REPOSITORY_ROOT)
    assert_ci_workflow_includes_release_checks(REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml")


def test_release_readiness_fails_when_required_paths_are_missing(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()

    with pytest.raises(AssertionError, match="Missing release readiness paths"):
        assert_required_paths_exist(tmp_path)
