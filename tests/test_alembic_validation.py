from hydra.adapters.alembic_validation import validate_alembic_configuration


def test_alembic_configuration_is_valid() -> None:
    script_location, heads, table_count = validate_alembic_configuration()

    assert script_location.endswith("alembic")
    assert heads
    assert table_count > 0
