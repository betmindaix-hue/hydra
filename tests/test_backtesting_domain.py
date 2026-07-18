from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hydra.domain.backtesting import (
    BacktestDirection,
    BacktestId,
    BacktestMetrics,
    BacktestResult,
    BacktestTimeRange,
    EquityCurvePoint,
    ResearchSignal,
    SimulatedPosition,
    SimulatedTrade,
)
from hydra.domain.market_data import DataSourceDescriptor, Market, Symbol, Timeframe


def test_backtest_id_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        BacktestId("   ")


def test_backtest_time_range_rejects_start_not_before_end() -> None:
    timestamp = datetime(2026, 7, 18, 10, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="start must be before end"):
        BacktestTimeRange(start=timestamp, end=timestamp)


def test_research_signal_validates_timestamp_and_direction() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ResearchSignal(
            timestamp=datetime(2026, 7, 18, 10, 0),
            direction=BacktestDirection.BUY,
        )

    with pytest.raises(ValueError, match="BacktestDirection"):
        ResearchSignal(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            direction="buy",  # type: ignore[arg-type]
        )


def test_simulated_trade_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        SimulatedTrade(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            direction=BacktestDirection.BUY,
            quantity=0,
            price=100,
        )


def test_simulated_trade_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="price must be non-negative"):
        SimulatedTrade(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            direction=BacktestDirection.SELL,
            quantity=1,
            price=-1,
        )


def test_equity_curve_point_rejects_negative_equity() -> None:
    with pytest.raises(ValueError, match="equity must be non-negative"):
        EquityCurvePoint(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            equity=-1,
            cash=100,
            position_quantity=0,
        )


def test_backtest_metrics_rejects_impossible_values() -> None:
    with pytest.raises(ValueError, match="total_return cannot be less than -1"):
        BacktestMetrics(
            initial_cash=1000,
            ending_cash=0,
            ending_equity=0,
            total_return=-1.5,
            max_drawdown=0.5,
            trade_count=1,
        )

    with pytest.raises(ValueError, match="max_drawdown must stay between 0 and 1"):
        BacktestMetrics(
            initial_cash=1000,
            ending_cash=1000,
            ending_equity=1000,
            total_return=0,
            max_drawdown=1.1,
            trade_count=0,
        )


def test_backtest_result_stores_simulated_trades_and_metrics() -> None:
    time_range = BacktestTimeRange(
        start=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        end=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
    )
    trade = SimulatedTrade(
        timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        direction=BacktestDirection.BUY,
        quantity=2,
        price=100,
    )
    metrics = BacktestMetrics(
        initial_cash=1000,
        ending_cash=0,
        ending_equity=1100,
        total_return=0.1,
        max_drawdown=0.0,
        trade_count=1,
    )
    result = BacktestResult(
        backtest_id=BacktestId("b3-demo"),
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        time_range=time_range,
        source=DataSourceDescriptor(name="fixture-series"),
        simulated_trades=(trade,),
        equity_curve=(
            EquityCurvePoint(
                timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
                equity=1000,
                cash=800,
                position_quantity=2,
            ),
        ),
        metrics=metrics,
        final_position=SimulatedPosition(
            quantity=2,
            average_entry_price=100,
            opened_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        ),
        signal_count=1,
    )

    assert str(result.backtest_id) == "b3-demo"
    assert result.simulated_trades == (trade,)
    assert result.metrics is metrics
    assert result.source is not None
    assert result.source.name == "fixture-series"
