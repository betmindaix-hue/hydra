from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hydra.application.strategy_research_dto import (
    StrategyResearchError,
    StrategyResearchRequest,
    StrategyResearchResult,
)
from hydra.domain.backtesting import BacktestDirection, BacktestTimeRange, ResearchSignal
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


def test_parameter_keys_are_stripped_and_none_values_are_allowed() -> None:
    request = StrategyResearchRequest(
        research_id="b4-parameters",
        market_data_series=make_series(),
        parameters={"  window  ": 5, "mode": None},
    )

    assert dict(request.parameters) == {"window": 5, "mode": None}


def test_with_time_range_returns_new_request_with_same_identity_and_parameters() -> None:
    request = StrategyResearchRequest(
        research_id="b4-range-copy",
        market_data_series=make_series(),
        parameters={"window": 5},
    )
    updated = request.with_time_range(
        start_timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        end_timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
    )

    assert updated is not request
    assert updated.research_id == request.research_id
    assert updated.market_data_series is request.market_data_series
    assert dict(updated.parameters) == {"window": 5}
    assert updated.start_timestamp == datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    assert updated.end_timestamp == datetime(2026, 7, 18, 10, 5, tzinfo=UTC)


def test_strategy_research_error_normalizes_fields_and_validates_timestamps() -> None:
    error = StrategyResearchError(
        message="  duplicate signal  ",
        field_name="  signals  ",
    )

    assert error.message == "duplicate signal"
    assert error.field_name == "signals"

    with pytest.raises(ValueError, match="field_name cannot be blank"):
        StrategyResearchError(message="duplicate signal", field_name="   ")

    with pytest.raises(ValueError, match="timezone-aware"):
        StrategyResearchError(
            message="duplicate signal",
            signal_timestamp=datetime(2026, 7, 18, 10, 0),
        )


def test_strategy_research_result_exposes_success_and_backtest_handoff() -> None:
    series = make_series()
    time_range = BacktestTimeRange(
        start=series.bars[0].timestamp,
        end=datetime(2026, 7, 18, 10, 1, tzinfo=UTC),
    )
    result = StrategyResearchResult(
        research_id="b4-result",
        market_data_series=series,
        time_range=time_range,
        signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.BUY,
            ),
        ),
        selected_bar_count=1,
        rejected_signal_count=0,
    )

    backtest_request = result.to_backtest_request(
        backtest_id="b4-backtest",
        initial_cash=1000,
    )

    assert result.successful is True
    assert backtest_request.backtest_id == "b4-backtest"
    assert backtest_request.research_signals == result.signals
    assert backtest_request.start_timestamp == time_range.start
    assert backtest_request.end_timestamp == time_range.end


def test_strategy_research_result_rejects_invalid_counts_and_handoff_preconditions() -> None:
    series = make_series()

    with pytest.raises(ValueError, match="selected_bar_count must be non-negative"):
        StrategyResearchResult(
            research_id="b4-negative-selected",
            market_data_series=series,
            selected_bar_count=-1,
        )

    with pytest.raises(ValueError, match="rejected_signal_count must be non-negative"):
        StrategyResearchResult(
            research_id="b4-negative-rejected",
            market_data_series=series,
            rejected_signal_count=-1,
        )

    failed_result = StrategyResearchResult(
        research_id="b4-errors",
        market_data_series=series,
        errors=(StrategyResearchError(message="out-of-range"),),
    )
    assert failed_result.successful is False

    with pytest.raises(ValueError, match="error-free before backtest handoff"):
        failed_result.to_backtest_request(backtest_id="b4-backtest", initial_cash=1000)

    with pytest.raises(ValueError, match="time_range is required"):
        StrategyResearchResult(
            research_id="b4-no-range",
            market_data_series=series,
        ).to_backtest_request(backtest_id="b4-backtest", initial_cash=1000)
