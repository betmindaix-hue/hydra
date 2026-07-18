from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hydra.application.strategy_research_dto import StrategyResearchRequest
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_series() -> MarketDataSeries:
    return MarketDataSeries(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=(
            OHLCVBar(
                symbol=Symbol("btcusdt"),
                market=Market("spot"),
                timeframe=Timeframe.MINUTE_1,
                timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
                open_price=100,
                high_price=101,
                low_price=99,
                close_price=100,
                volume=10,
            ),
        ),
        source=DataSourceDescriptor(name="research-fixture"),
    )


def test_research_id_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        StrategyResearchRequest(
            research_id="   ",
            market_data_series=make_series(),
        )


def test_timestamps_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        StrategyResearchRequest(
            research_id="b4-time",
            market_data_series=make_series(),
            start_timestamp=datetime(2026, 7, 18, 10, 0),
        )


def test_start_timestamp_must_be_before_end_timestamp() -> None:
    timestamp = datetime(2026, 7, 18, 10, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="must be before end_timestamp"):
        StrategyResearchRequest(
            research_id="b4-range",
            market_data_series=make_series(),
            start_timestamp=timestamp,
            end_timestamp=timestamp,
        )


def test_parameter_keys_cannot_be_blank() -> None:
    with pytest.raises(ValueError, match="parameter keys cannot be blank"):
        StrategyResearchRequest(
            research_id="b4-parameters",
            market_data_series=make_series(),
            parameters={" ": 5},
        )


def test_unsupported_parameter_value_types_are_rejected() -> None:
    with pytest.raises(ValueError, match="simple primitives"):
        StrategyResearchRequest(
            research_id="b4-types",
            market_data_series=make_series(),
            parameters={"window": [5]},  # type: ignore[dict-item]
        )


def test_parameters_are_defensively_copied_and_immutable() -> None:
    parameters = {"window": 5, "enabled": True}
    request = StrategyResearchRequest(
        research_id="b4-copy",
        market_data_series=make_series(),
        parameters=parameters,
    )

    parameters["window"] = 10

    assert request.parameters["window"] == 5
    with pytest.raises(TypeError):
        request.parameters["new"] = 1  # type: ignore[index]
