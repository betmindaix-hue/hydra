from __future__ import annotations

import runpy
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy import text

from hydra.infrastructure.database import session as session_module
from hydra.ports.runtime_settings import RuntimeSettings
from hydra.shared.runtime_environment import RuntimeEnvironment

SESSION_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "hydra"
    / "infrastructure"
    / "database"
    / "session.py"
)


class StaticSettingsPort:
    def __init__(self, settings: RuntimeSettings) -> None:
        self._settings = settings
        self.load_calls = 0

    def load(self) -> RuntimeSettings:
        self.load_calls += 1
        return self._settings


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def build_runtime_settings(database_url: str = "sqlite+pysqlite:///:memory:") -> RuntimeSettings:
    return RuntimeSettings(
        app_name="HYDRA",
        app_version="0.1.0",
        environment=RuntimeEnvironment.TEST,
        api_prefix="/api/v1",
        database_url=database_url,
        redis_url="redis://localhost:6379/0",
        log_level="INFO",
    )


def test_session_module_import_does_not_create_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    create_engine_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_create_engine(*args: object, **kwargs: object) -> object:
        create_engine_calls.append((args, kwargs))
        return object()

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)

    runpy.run_path(str(SESSION_MODULE_PATH))

    assert create_engine_calls == []


def test_build_engine_uses_database_url_from_settings_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_port = StaticSettingsPort(build_runtime_settings("sqlite+pysqlite:///./hydra-test.db"))
    captured: dict[str, object] = {}
    sentinel_engine = object()

    def fake_create_engine(database_url: str, *, pool_pre_ping: bool) -> object:
        captured["database_url"] = database_url
        captured["pool_pre_ping"] = pool_pre_ping
        return sentinel_engine

    monkeypatch.setattr(session_module, "create_engine", fake_create_engine)

    engine = session_module.build_engine(settings_port)

    assert engine is sentinel_engine
    assert settings_port.load_calls == 1
    assert captured == {
        "database_url": "sqlite+pysqlite:///./hydra-test.db",
        "pool_pre_ping": True,
    }


def test_build_session_factory_creates_configured_sessionmaker() -> None:
    settings_port = StaticSettingsPort(build_runtime_settings())

    session_factory = session_module.build_session_factory(settings_port)

    assert settings_port.load_calls == 1
    assert session_factory.kw["autoflush"] is False
    assert session_factory.kw["autocommit"] is False
    assert session_factory.kw["expire_on_commit"] is False
    assert session_factory.kw["bind"] is not None


def test_session_factory_is_usable_in_a_controlled_sqlite_scenario() -> None:
    settings_port = StaticSettingsPort(build_runtime_settings())
    session_factory = session_module.build_session_factory(settings_port)

    with session_factory() as db:
        result = db.execute(text("select 1")).scalar_one()

    assert settings_port.load_calls == 1
    assert result == 1


def test_get_db_yields_session_and_closes_it(monkeypatch: pytest.MonkeyPatch) -> None:
    settings_port = StaticSettingsPort(build_runtime_settings())
    fake_session = FakeSession()

    monkeypatch.setattr(session_module, "build_session_factory", lambda _: lambda: fake_session)

    generator = session_module.get_db(settings_port)

    yielded_session = next(generator)

    assert yielded_session is fake_session

    with pytest.raises(StopIteration):
        next(generator)

    assert fake_session.closed is True
