from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE_PATH = REPOSITORY_ROOT / ".env.example"
ENV_EXAMPLE_PATHS = (
    ENV_EXAMPLE_PATH,
    REPOSITORY_ROOT / ".env.local.example",
    REPOSITORY_ROOT / ".env.test.example",
)
REQUIRED_ENV_KEYS = (
    "HYDRA_APP_NAME",
    "HYDRA_APP_VERSION",
    "HYDRA_ENVIRONMENT",
    "HYDRA_API_PREFIX",
    "HYDRA_DATABASE_URL",
    "HYDRA_REDIS_URL",
    "HYDRA_LOG_LEVEL",
)
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

    for key in REQUIRED_ENV_KEYS:
        assert f"{key}=" in contents

    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        assert separator == "=", f"{env_example_path} contains a malformed line: {raw_line}"
        assert value, f"{env_example_path} must define a value for {key}"
        assert (
            "<" in value and ">" in value
        ), f"{env_example_path} must use placeholder values for {key}"

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
    for env_example_path in ENV_EXAMPLE_PATHS:
        assert_env_example_uses_placeholders(env_example_path)
    assert_no_obvious_secrets()
    assert_no_forbidden_source_keywords()


if __name__ == "__main__":
    main()
