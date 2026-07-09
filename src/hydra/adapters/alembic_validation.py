from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from hydra.adapters import sqlalchemy_models  # noqa: F401
from hydra.adapters.runtime_settings import PydanticRuntimeSettingsAdapter
from hydra.infrastructure.database.base import Base


def validate_alembic_configuration() -> tuple[str, tuple[str, ...], int]:
    repository_root = Path(__file__).resolve().parents[3]
    config_path = repository_root / "alembic.ini"
    if not config_path.exists():
        raise FileNotFoundError(f"Alembic config not found: {config_path}")

    config = Config(str(config_path))
    runtime_settings = PydanticRuntimeSettingsAdapter().load()
    config.set_main_option("sqlalchemy.url", runtime_settings.database_url)

    script_directory = ScriptDirectory.from_config(config)
    heads = tuple(script_directory.get_heads())
    table_count = len(Base.metadata.tables)

    if not heads:
        raise RuntimeError("Alembic validation failed: no migration heads were discovered.")
    if table_count == 0:
        raise RuntimeError("Alembic validation failed: SQLAlchemy metadata is empty.")

    return script_directory.dir, heads, table_count


def main() -> None:
    script_location, heads, table_count = validate_alembic_configuration()
    print(
        "Alembic configuration is valid. "
        f"script_location={script_location}, heads={heads}, tables={table_count}"
    )


if __name__ == "__main__":
    main()
