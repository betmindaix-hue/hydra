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


def test_simulated_trade_rejects_hold_direction() -> None:
    with pytest.raises(ValueError, match="cannot be HOLD"):
        SimulatedTrade(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            direction=BacktestDirection.HOLD,
            quantity=1,
            price=100,
        )


def test_simulated_position_rejects_inconsistent_closed_state() -> None:
    with pytest.raises(ValueError, match="must be 0 when quantity is 0"):
        SimulatedPosition(quantity=0, average_entry_price=1)

    with pytest.raises(ValueError, match="must be None when quantity is 0"):
        SimulatedPosition(
            quantity=0,
            average_entry_price=0,
            opened_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        )


def test_simulated_position_rejects_inconsistent_open_state() -> None:
    with pytest.raises(ValueError, match="must be positive when quantity is open"):
        SimulatedPosition(
            quantity=1,
            average_entry_price=0,
            opened_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="opened_at is required"):
        SimulatedPosition(quantity=1, average_entry_price=100)

    with pytest.raises(ValueError, match="timezone-aware"):
        SimulatedPosition(
            quantity=1,
            average_entry_price=100,
            opened_at=datetime(2026, 7, 18, 10, 0),
        )


def test_equity_curve_point_rejects_negative_equity() -> None:
    with pytest.raises(ValueError, match="equity must be non-negative"):
        EquityCurvePoint(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            equity=-1,
            cash=100,
            position_quantity=0,
        )


@pytest.mark.parametrize(
    ("field_name", "cash", "position_quantity", "message"),
    (
        ("cash", -1, 0, "cash must be non-negative"),
        ("position_quantity", 0, -1, "position_quantity must be non-negative"),
    ),
)
def test_equity_curve_point_rejects_negative_cash_and_position_quantity(
    field_name: str,
    cash: float,
    position_quantity: float,
    message: str,
) -> None:
    del field_name

    with pytest.raises(ValueError, match=message):
        EquityCurvePoint(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            equity=1000,
            cash=cash,
            position_quantity=position_quantity,
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


@pytest.mark.parametrize(
    ("initial_cash", "ending_cash", "ending_equity", "trade_count", "message"),
    (
        (0, 1000, 1000, 0, "initial_cash must be positive"),
        (1000, -1, 1000, 0, "ending_cash must be non-negative"),
        (1000, 1000, -1, 0, "ending_equity must be non-negative"),
        (1000, 1000, 1000, -1, "trade_count must be non-negative"),
    ),
)
def test_backtest_metrics_rejects_invalid_cash_equity_and_trade_counts(
    initial_cash: float,
    ending_cash: float,
    ending_equity: float,
    trade_count: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        BacktestMetrics(
            initial_cash=initial_cash,
            ending_cash=ending_cash,
            ending_equity=ending_equity,
            total_return=0,
            max_drawdown=0,
            trade_count=trade_count,
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


def test_backtest_result_requires_equity_curve_metrics_and_non_negative_signal_count() -> None:
    time_range = BacktestTimeRange(
        start=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        end=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
    )
    metrics = BacktestMetrics(
        initial_cash=1000,
        ending_cash=1000,
        ending_equity=1000,
        total_return=0,
        max_drawdown=0,
        trade_count=0,
    )
    equity_curve = (
        EquityCurvePoint(
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            equity=1000,
            cash=1000,
            position_quantity=0,
        ),
    )

    with pytest.raises(ValueError, match="at least one equity curve point"):
        BacktestResult(
            backtest_id=BacktestId("b3-missing-curve"),
            symbol=Symbol("btcusdt"),
            market=Market("spot"),
            timeframe=Timeframe.MINUTE_1,
            time_range=time_range,
            source=DataSourceDescriptor(name="fixture-series"),
            equity_curve=(),
            metrics=metrics,
        )

    with pytest.raises(ValueError, match="metrics are required"):
        BacktestResult(
            backtest_id=BacktestId("b3-missing-metrics"),
            symbol=Symbol("btcusdt"),
            market=Market("spot"),
            timeframe=Timeframe.MINUTE_1,
            time_range=time_range,
            source=DataSourceDescriptor(name="fixture-series"),
            equity_curve=equity_curve,
            metrics=None,
        )

    with pytest.raises(ValueError, match="signal_count must be non-negative"):
        BacktestResult(
            backtest_id=BacktestId("b3-negative-signals"),
            symbol=Symbol("btcusdt"),
            market=Market("spot"),
            timeframe=Timeframe.MINUTE_1,
            time_range=time_range,
            source=DataSourceDescriptor(name="fixture-series"),
            equity_curve=equity_curve,
            metrics=metrics,
            signal_count=-1,
        )
