from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hydra.adapters.strategy_research import (
    DeterministicFixtureStrategyResearchProvider,
    FixtureSignalInstruction,
)
from hydra.application.backtesting_dto import BacktestRequest
from hydra.application.strategy_research_dto import (
    StrategyResearchRequest,
    StrategyResearchResult,
)
from hydra.application.strategy_research_service import OfflineStrategyResearchService
from hydra.domain.backtesting import BacktestDirection
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_bar(index: int, close_price: float = 100.0) -> OHLCVBar:
    timestamp = datetime(2026, 7, 18, 12, 0, tzinfo=UTC) + timedelta(minutes=index)

    return OHLCVBar(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        timestamp=timestamp,
        open_price=close_price,
        high_price=close_price + 1,
        low_price=close_price - 1,
        close_price=close_price,
        volume=10,
    )


def make_series(bar_count: int = 4) -> MarketDataSeries:
    bars = tuple(make_bar(index, close_price=100 + index) for index in range(bar_count))

    return MarketDataSeries(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=bars,
        source=DataSourceDescriptor(name="fixture-provider-series"),
    )


def make_request(
    series: MarketDataSeries,
    *,
    research_id: str = "b5-fixture",
    start_timestamp: datetime | None = None,
    end_timestamp: datetime | None = None,
) -> StrategyResearchRequest:
    return StrategyResearchRequest(
        research_id=research_id,
        market_data_series=series,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        parameters={"window": 3},
    )


def test_creates_buy_signal_at_selected_bar_index() -> None:
    series = make_series()
    request = make_request(series)
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(FixtureSignalInstruction(bar_index=1, direction=BacktestDirection.BUY),)
    )

    signals = provider.generate_signals(request)

    assert len(signals) == 1
    assert signals[0].timestamp == series.bars[1].timestamp
    assert signals[0].direction is BacktestDirection.BUY


def test_creates_sell_signal_at_selected_bar_index() -> None:
    series = make_series()
    request = make_request(series)
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(FixtureSignalInstruction(bar_index=2, direction=BacktestDirection.SELL),)
    )

    signals = provider.generate_signals(request)

    assert len(signals) == 1
    assert signals[0].timestamp == series.bars[2].timestamp
    assert signals[0].direction is BacktestDirection.SELL


def test_creates_hold_signal_at_selected_bar_index() -> None:
    series = make_series()
    request = make_request(series)
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.HOLD),)
    )

    signals = provider.generate_signals(request)

    assert len(signals) == 1
    assert signals[0].timestamp == series.bars[0].timestamp
    assert signals[0].direction is BacktestDirection.HOLD


def test_returns_signals_in_deterministic_bar_index_order() -> None:
    series = make_series()
    request = make_request(series)
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(
            FixtureSignalInstruction(bar_index=2, direction=BacktestDirection.SELL),
            FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.BUY),
            FixtureSignalInstruction(bar_index=1, direction=BacktestDirection.HOLD),
        )
    )

    signals = provider.generate_signals(request)

    assert tuple(signal.timestamp for signal in signals) == (
        series.bars[0].timestamp,
        series.bars[1].timestamp,
        series.bars[2].timestamp,
    )
    assert tuple(signal.direction for signal in signals) == (
        BacktestDirection.BUY,
        BacktestDirection.HOLD,
        BacktestDirection.SELL,
    )


def test_preserves_instruction_notes_after_normalization() -> None:
    series = make_series()
    request = make_request(series)
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(
            FixtureSignalInstruction(
                bar_index=1,
                direction=BacktestDirection.BUY,
                note="  first entry  ",
            ),
        )
    )

    signals = provider.generate_signals(request)

    assert signals[0].note == "first entry"


def test_accepts_empty_instruction_tuple_and_returns_zero_signals() -> None:
    provider = DeterministicFixtureStrategyResearchProvider()

    signals = provider.generate_signals(make_request(make_series()))

    assert signals == ()


def test_rejects_negative_bar_index() -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        FixtureSignalInstruction(bar_index=-1, direction=BacktestDirection.BUY)


def test_rejects_non_integer_bar_index() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        FixtureSignalInstruction(
            bar_index=1.5,  # type: ignore[arg-type]
            direction=BacktestDirection.BUY,
        )


def test_rejects_invalid_direction() -> None:
    with pytest.raises(ValueError, match="BacktestDirection"):
        FixtureSignalInstruction(
            bar_index=0,
            direction="buy",  # type: ignore[arg-type]
        )


def test_rejects_duplicate_bar_index_values() -> None:
    with pytest.raises(ValueError, match="must be unique"):
        DeterministicFixtureStrategyResearchProvider(
            instructions=(
                FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.BUY),
                FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.SELL),
            )
        )


def test_raises_clear_error_when_bar_index_is_outside_selected_bars() -> None:
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(FixtureSignalInstruction(bar_index=2, direction=BacktestDirection.BUY),)
    )

    with pytest.raises(ValueError, match="outside the selected bar window of 2 bars"):
        provider.generate_signals(make_request(make_series(bar_count=2)))


def test_respects_time_range_and_treats_bar_indexes_as_relative_to_selected_bars() -> None:
    series = make_series()
    request = make_request(
        series,
        start_timestamp=series.bars[1].timestamp,
        end_timestamp=series.bars[2].timestamp,
    )
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(
            FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.BUY),
            FixtureSignalInstruction(bar_index=1, direction=BacktestDirection.SELL),
        )
    )

    signals = provider.generate_signals(request)

    assert tuple(signal.timestamp for signal in signals) == (
        series.bars[1].timestamp,
        series.bars[2].timestamp,
    )


def test_does_not_mutate_the_request() -> None:
    series = make_series()
    request = make_request(
        series,
        start_timestamp=series.bars[1].timestamp,
        end_timestamp=series.bars[3].timestamp,
    )
    baseline = (
        request.research_id,
        request.market_data_series,
        request.start_timestamp,
        request.end_timestamp,
        dict(request.parameters),
    )
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(FixtureSignalInstruction(bar_index=1, direction=BacktestDirection.BUY),)
    )

    provider.generate_signals(request)

    assert request.research_id == baseline[0]
    assert request.market_data_series == baseline[1]
    assert request.start_timestamp == baseline[2]
    assert request.end_timestamp == baseline[3]
    assert dict(request.parameters) == baseline[4]


def test_integrates_with_offline_strategy_research_service() -> None:
    series = make_series()
    request = make_request(series)
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(
            FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.BUY),
            FixtureSignalInstruction(
                bar_index=2,
                direction=BacktestDirection.SELL,
                note="fixture exit",
            ),
        )
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(request)

    assert result.successful is True
    assert result.selected_bar_count == 4
    assert tuple(signal.direction for signal in result.signals) == (
        BacktestDirection.BUY,
        BacktestDirection.SELL,
    )
    assert result.signals[1].note == "fixture exit"


def test_valid_result_can_be_explicitly_converted_to_backtest_request() -> None:
    series = make_series()
    provider = DeterministicFixtureStrategyResearchProvider(
        instructions=(FixtureSignalInstruction(bar_index=1, direction=BacktestDirection.BUY),)
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(make_request(series, research_id="b5-handoff"))
    backtest_request = result.to_backtest_request(
        backtest_id="b5-backtest",
        initial_cash=1000,
    )

    assert isinstance(backtest_request, BacktestRequest)
    assert backtest_request.research_signals == result.signals
    assert backtest_request.start_timestamp == series.bars[0].timestamp
    assert backtest_request.end_timestamp == series.bars[-1].timestamp


def test_service_execution_does_not_run_a_backtest_automatically() -> None:
    service = OfflineStrategyResearchService(
        DeterministicFixtureStrategyResearchProvider(
            instructions=(FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.HOLD),)
        )
    )

    result = service.execute(make_request(make_series(), research_id="b5-no-backtest"))

    assert isinstance(result, StrategyResearchResult)
    assert not isinstance(result, BacktestRequest)
