from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE_PATH = REPOSITORY_ROOT / ".env.example"
SOURCE_DIRECTORIES = (
    REPOSITORY_ROOT / "src",
    REPOSITORY_ROOT / "tools",
    REPOSITORY_ROOT / ".github",
)
OBVIOUS_SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
)
FORBIDDEN_SOURCE_PATTERNS = (
    re.compile(r"\bbinance\b", re.IGNORECASE),
    re.compile(r"\bcoinbase\b", re.IGNORECASE),
    re.compile(r"\bkraken\b", re.IGNORECASE),
    re.compile(r"\bbybit\b", re.IGNORECASE),
    re.compile(r"\bccxt\b", re.IGNORECASE),
    re.compile(r"\bwebsocket\b", re.IGNORECASE),
    re.compile(r"\bapi_secret\b", re.IGNORECASE),
    re.compile(r"\bsecret_key\b", re.IGNORECASE),
)


def assert_env_example_uses_placeholders(env_example_path: Path = ENV_EXAMPLE_PATH) -> None:
    contents = env_example_path.read_text(encoding="utf-8")

    assert "<db_password>" in contents
    assert "<environment>" in contents
    assert "supersecret" not in contents
    assert "ghp_" not in contents
    assert "AKIA" not in contents


def assert_no_obvious_secrets(paths: tuple[Path, ...] = SOURCE_DIRECTORIES) -> None:
    for file_path in iter_text_files(paths):
        text = file_path.read_text(encoding="utf-8")
        for pattern in OBVIOUS_SECRET_PATTERNS:
            if pattern.search(text):
                raise AssertionError(
                    f"Potential secret pattern '{pattern.pattern}' found in {file_path}"
                )


def assert_no_forbidden_source_keywords(paths: tuple[Path, ...] = SOURCE_DIRECTORIES) -> None:
    for file_path in iter_text_files(paths):
        text = file_path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_SOURCE_PATTERNS:
            if pattern.search(text):
                raise AssertionError(
                    f"Forbidden source keyword pattern '{pattern.pattern}' found in {file_path}"
                )


def iter_text_files(paths: tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
            continue
        files.extend(
            sorted(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix in {".py", ".yml", ".yaml", ".md"}
            )
        )
    return files


def main() -> None:
    assert_env_example_uses_placeholders()
    assert_no_obvious_secrets()
    assert_no_forbidden_source_keywords()


if __name__ == "__main__":
    main()
