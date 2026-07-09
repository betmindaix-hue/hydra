from contextvars import ContextVar, Token
from uuid import uuid4

_correlation_id: ContextVar[str | None] = ContextVar("hydra_correlation_id", default=None)


def generate_correlation_id() -> str:
    return str(uuid4())


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def set_correlation_id(value: str) -> Token[str | None]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)
