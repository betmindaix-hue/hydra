from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from hydra.ports.runtime_settings import RuntimeSettingsPort


def build_engine(settings_port: RuntimeSettingsPort) -> Engine:
    runtime_settings = settings_port.load()
    return create_engine(runtime_settings.database_url, pool_pre_ping=True)


def build_session_factory(settings_port: RuntimeSettingsPort) -> sessionmaker[Session]:
    engine = build_engine(settings_port)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db(settings_port: RuntimeSettingsPort) -> Generator[Session, None, None]:
    session_factory = build_session_factory(settings_port)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
