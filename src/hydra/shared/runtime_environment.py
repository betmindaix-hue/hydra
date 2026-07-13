from enum import StrEnum


class RuntimeEnvironment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION_LIKE = "production-like"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(member.value for member in cls)
