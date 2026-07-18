from __future__ import annotations

from datetime import UTC, datetime

from hydra.application.backtesting_dto import BacktestRequest
from hydra.application.backtesting_service import OfflineBacktestingService
from hydra.domain.backtesting import BacktestDirection, ResearchSignal
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_bar(
    minute: int,
    *,
    close_price: float,
    open_price: float | None = None,
    high_price: float | None = None,
    low_price: float | None = None,
) -> OHLCVBar:
    base_price = open_price if open_price is not None else close_price
    return OHLCVBar(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        timestamp=datetime(2026, 7, 18, 10, minute, tzinfo=UTC),
        open_price=base_price,
        high_price=high_price if high_price is not None else max(base_price, close_price),
        low_price=low_price if low_price is not None else min(base_price, close_price),
        close_price=close_price,
        volume=10,
    )


def make_series(*bars: OHLCVBar) -> MarketDataSeries:
    return MarketDataSeries(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=bars,
        source=DataSourceDescriptor(name="offline-fixture-series"),
    )


def test_runs_simple_offline_backtest_over_valid_market_data_series() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=110),
    )
    request = BacktestRequest(
        backtest_id="b3-basic",
        market_data_series=series,
        initial_cash=1000,
        research_signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.BUY,
            ),
        ),
    )

    summary = service.execute(request)

    assert summary.result is not None
    assert summary.result.metrics is not None
    assert summary.processed_bar_count == 2
    assert summary.simulated_trade_count == 1
    assert summary.result.metrics.total_return == 0.1


def test_buy_signal_creates_simulated_long_position_and_trade() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=105),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-buy",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert len(summary.result.simulated_trades) == 1
    assert summary.result.final_position.is_open is True
    assert summary.result.final_position.quantity == 10


def test_sell_signal_exits_simulated_position_and_trade() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=110),
        make_bar(2, close_price=110),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-sell",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                ),
                ResearchSignal(
                    timestamp=series.bars[1].timestamp,
                    direction=BacktestDirection.SELL,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert summary.result.metrics is not None
    assert len(summary.result.simulated_trades) == 2
    assert summary.result.final_position.is_open is False
    assert summary.result.metrics.ending_cash == 1100


def test_hold_signal_creates_no_trade() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=101),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-hold",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.HOLD,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert summary.result.metrics is not None
    assert not summary.result.simulated_trades
    assert summary.result.metrics.ending_cash == 1000


def test_request_with_no_market_data_is_reported() -> None:
    service = OfflineBacktestingService()
    empty_series = MarketDataSeries(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=(),
        source=DataSourceDescriptor(name="empty-series"),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-empty",
            market_data_series=empty_series,
            initial_cash=1000,
        )
    )

    assert summary.result is None
    assert len(summary.errors) == 1
    assert summary.errors[0].field_name == "market_data_series"


def test_initial_cash_must_be_positive() -> None:
    service = OfflineBacktestingService()
    series = make_series(make_bar(0, close_price=100), make_bar(1, close_price=100))

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-no-cash",
            market_data_series=series,
            initial_cash=0,
        )
    )

    assert summary.result is None
    assert len(summary.errors) == 1
    assert summary.errors[0].field_name == "initial_cash"


def test_result_includes_equity_curve() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=120),
        make_bar(2, close_price=120),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-curve",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert len(summary.result.equity_curve) == 3
    assert summary.result.equity_curve[-1].equity == 1200


def test_total_return_is_deterministic() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=150),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-return",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert summary.result.metrics is not None
    assert summary.result.metrics.total_return == 0.5


def test_max_drawdown_is_deterministic() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=80),
        make_bar(2, close_price=120),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-drawdown",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert summary.result.metrics is not None
    assert round(summary.result.metrics.max_drawdown, 4) == 0.2
    assert round(summary.result.metrics.total_return, 4) == 0.2


def test_signals_outside_dataset_time_range_are_reported_and_ignored() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=110),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-ignored-signal",
            market_data_series=series,
            initial_cash=1000,
            research_signals=(
                ResearchSignal(
                    timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
                    direction=BacktestDirection.BUY,
                ),
            ),
        )
    )

    assert summary.result is not None
    assert summary.ignored_signal_count == 1
    assert len(summary.errors) == 1
    assert not summary.result.simulated_trades


def test_service_applies_requested_time_range() -> None:
    service = OfflineBacktestingService()
    series = make_series(
        make_bar(0, close_price=100),
        make_bar(1, close_price=110),
        make_bar(2, close_price=120),
    )

    summary = service.execute(
        BacktestRequest(
            backtest_id="b3-window",
            market_data_series=series,
            initial_cash=1000,
            start_timestamp=series.bars[1].timestamp,
            end_timestamp=datetime(2026, 7, 18, 10, 2, 1, tzinfo=UTC),
        )
    )

    assert summary.result is not None
    assert summary.processed_bar_count == 2
    assert summary.result.time_range.start == series.bars[1].timestamp
