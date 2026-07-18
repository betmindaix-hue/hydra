from __future__ import annotations

from builtins import open as builtins_open
from datetime import UTC, datetime

import pytest

from hydra.application.backtesting_dto import BacktestRunSummary
from hydra.application.backtesting_service import OfflineBacktestingService
from hydra.application.research_reporting_dto import (
    ResearchReportGenerationResult,
    ResearchReportRequest,
)
from hydra.application.research_reporting_service import OfflineResearchReportingService
from hydra.application.strategy_research_dto import (
    StrategyResearchError,
    StrategyResearchResult,
)
from hydra.application.strategy_research_service import OfflineStrategyResearchService
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
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_series(
    *,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
) -> MarketDataSeries:
    bars = (
        OHLCVBar(
            symbol=Symbol(symbol),
            market=Market(market),
            timeframe=timeframe,
            timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            open_price=100,
            high_price=101,
            low_price=99,
            close_price=100,
            volume=10,
        ),
        OHLCVBar(
            symbol=Symbol(symbol),
            market=Market(market),
            timeframe=timeframe,
            timestamp=datetime(2026, 7, 18, 10, 1, tzinfo=UTC),
            open_price=100,
            high_price=111,
            low_price=99,
            close_price=110,
            volume=12,
        ),
        OHLCVBar(
            symbol=Symbol(symbol),
            market=Market(market),
            timeframe=timeframe,
            timestamp=datetime(2026, 7, 18, 10, 2, tzinfo=UTC),
            open_price=110,
            high_price=121,
            low_price=109,
            close_price=120,
            volume=14,
        ),
    )

    return MarketDataSeries(
        symbol=Symbol(symbol),
        market=Market(market),
        timeframe=timeframe,
        bars=bars,
        source=DataSourceDescriptor(name="reporting-series"),
    )


def make_backtest_result(
    *,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
    open_position: bool = False,
    signal_count: int = 2,
    simulated_trades: tuple[SimulatedTrade, ...] | None = None,
    metrics: BacktestMetrics | None = None,
) -> BacktestResult:
    series = make_series(symbol=symbol, market=market, timeframe=timeframe)
    time_range = BacktestTimeRange(
        start=series.bars[0].timestamp,
        end=series.bars[-1].timestamp,
    )
    resolved_trades = simulated_trades
    if resolved_trades is None:
        if open_position:
            resolved_trades = (
                SimulatedTrade(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                    quantity=10,
                    price=100,
                ),
            )
        else:
            resolved_trades = (
                SimulatedTrade(
                    timestamp=series.bars[0].timestamp,
                    direction=BacktestDirection.BUY,
                    quantity=10,
                    price=100,
                ),
                SimulatedTrade(
                    timestamp=series.bars[1].timestamp,
                    direction=BacktestDirection.SELL,
                    quantity=10,
                    price=110,
                ),
            )

    resolved_metrics = metrics or BacktestMetrics(
        initial_cash=1000,
        ending_cash=1100 if not open_position else 0,
        ending_equity=1100 if not open_position else 1200,
        total_return=0.1 if not open_position else 0.2,
        max_drawdown=0.1,
        trade_count=len(resolved_trades),
    )
    final_position = (
        SimulatedPosition(
            quantity=10,
            average_entry_price=100,
            opened_at=series.bars[0].timestamp,
        )
        if open_position
        else SimulatedPosition()
    )

    return BacktestResult(
        backtest_id=BacktestId("b6-backtest"),
        symbol=series.symbol,
        market=series.market,
        timeframe=series.timeframe,
        time_range=time_range,
        source=series.source,
        simulated_trades=resolved_trades,
        equity_curve=(
            EquityCurvePoint(
                timestamp=series.bars[0].timestamp,
                equity=1000,
                cash=1000 if not open_position else 0,
                position_quantity=0 if not open_position else 10,
            ),
            EquityCurvePoint(
                timestamp=series.bars[1].timestamp,
                equity=900 if not open_position else 1100,
                cash=900 if not open_position else 0,
                position_quantity=0 if not open_position else 10,
            ),
            EquityCurvePoint(
                timestamp=series.bars[2].timestamp,
                equity=resolved_metrics.ending_equity,
                cash=resolved_metrics.ending_cash,
                position_quantity=0 if not open_position else 10,
            ),
        ),
        metrics=resolved_metrics,
        final_position=final_position,
        signal_count=signal_count,
    )


def make_strategy_research_result(
    *,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
    rejected_signal_count: int = 1,
    errors: tuple[StrategyResearchError, ...] = (),
) -> StrategyResearchResult:
    series = make_series(symbol=symbol, market=market, timeframe=timeframe)
    time_range = BacktestTimeRange(
        start=series.bars[0].timestamp,
        end=series.bars[-1].timestamp,
    )

    return StrategyResearchResult(
        research_id="b6-research",
        market_data_series=series,
        time_range=time_range,
        signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.BUY,
            ),
            ResearchSignal(
                timestamp=series.bars[1].timestamp,
                direction=BacktestDirection.HOLD,
            ),
            ResearchSignal(
                timestamp=series.bars[2].timestamp,
                direction=BacktestDirection.SELL,
            ),
        ),
        errors=errors,
        selected_bar_count=3,
        rejected_signal_count=rejected_signal_count,
    )


def test_builds_report_from_backtest_result() -> None:
    service = OfflineResearchReportingService()
    result = service.generate(
        ResearchReportRequest(
            report_id="b6-report",
            backtest_result=make_backtest_result(),
        )
    )

    assert result.successful is True
    assert result.report is not None
    assert result.report.report_id.value == "b6-report"
    assert result.report.backtest_id.value == "b6-backtest"


def test_metrics_are_copied_from_backtest_result_metrics() -> None:
    backtest_result = make_backtest_result()
    assert backtest_result.metrics is not None
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-metrics",
            backtest_result=backtest_result,
        )
    )

    assert result.report is not None
    assert result.report.metrics.initial_cash == backtest_result.metrics.initial_cash
    assert result.report.metrics.ending_cash == backtest_result.metrics.ending_cash
    assert result.report.metrics.signal_count == backtest_result.signal_count


def test_equity_summary_uses_first_and_last_equity_curve_points() -> None:
    backtest_result = make_backtest_result()
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-equity-window",
            backtest_result=backtest_result,
        )
    )

    assert result.report is not None
    assert result.report.equity_curve.first_timestamp == backtest_result.equity_curve[0].timestamp
    assert result.report.equity_curve.last_timestamp == backtest_result.equity_curve[-1].timestamp
    assert result.report.equity_curve.starting_equity == backtest_result.equity_curve[0].equity
    assert result.report.equity_curve.ending_equity == backtest_result.equity_curve[-1].equity


def test_equity_summary_computes_min_and_max_equity() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-equity-range",
            backtest_result=make_backtest_result(),
        )
    )

    assert result.report is not None
    assert result.report.equity_curve.min_equity == 900
    assert result.report.equity_curve.max_equity == 1100


def test_trade_summary_counts_buy_and_sell_simulated_trades() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-trades",
            backtest_result=make_backtest_result(),
        )
    )

    assert result.report is not None
    assert result.report.simulated_trades.trade_count == 2
    assert result.report.simulated_trades.buy_count == 1
    assert result.report.simulated_trades.sell_count == 1


def test_trade_summary_handles_no_trades() -> None:
    backtest_result = make_backtest_result(
        simulated_trades=(),
        metrics=BacktestMetrics(
            initial_cash=1000,
            ending_cash=1000,
            ending_equity=1000,
            total_return=0,
            max_drawdown=0,
            trade_count=0,
        ),
        signal_count=0,
    )
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-no-trades",
            backtest_result=backtest_result,
        )
    )

    assert result.report is not None
    assert result.report.simulated_trades.trade_count == 0
    assert result.report.simulated_trades.first_trade_timestamp is None


def test_risk_snapshot_reflects_final_position_closed() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-risk-closed",
            backtest_result=make_backtest_result(open_position=False),
        )
    )

    assert result.report is not None
    assert result.report.risk.final_position_open is False
    assert result.report.risk.final_position_quantity == 0


def test_risk_snapshot_reflects_final_position_open() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-risk-open",
            backtest_result=make_backtest_result(open_position=True),
        )
    )

    assert result.report is not None
    assert result.report.risk.final_position_open is True
    assert result.report.risk.final_position_quantity == 10


def test_signal_summary_uses_backtest_result_signal_count() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-backtest-signals",
            backtest_result=make_backtest_result(signal_count=4),
        )
    )

    assert result.report is not None
    assert result.report.signals.backtest_signal_count == 4


def test_optional_strategy_research_result_adds_research_signal_counts() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-research-signals",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(),
        )
    )

    assert result.report is not None
    assert result.report.signals.research_signal_count == 3


def test_optional_strategy_research_result_counts_buy_sell_and_hold_signals() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-direction-counts",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(),
        )
    )

    assert result.report is not None
    assert result.report.signals.buy_signal_count == 1
    assert result.report.signals.sell_signal_count == 1
    assert result.report.signals.hold_signal_count == 1


def test_optional_strategy_research_result_includes_rejected_signal_count() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-rejected-count",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(rejected_signal_count=2),
        )
    )

    assert result.report is not None
    assert result.report.signals.rejected_signal_count == 2


def test_optional_strategy_research_result_includes_research_error_count() -> None:
    strategy_research_result = make_strategy_research_result(
        errors=(
            StrategyResearchError(message="signal duplicate"),
            StrategyResearchError(message="range mismatch"),
        )
    )
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-error-count",
            backtest_result=make_backtest_result(),
            strategy_research_result=strategy_research_result,
        )
    )

    assert result.report is not None
    assert result.report.signals.research_error_count == 2


def test_strategy_research_result_with_errors_does_not_fail_report_generation() -> None:
    strategy_research_result = make_strategy_research_result(
        errors=(StrategyResearchError(message="provider reported a soft error"),)
    )
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-soft-errors",
            backtest_result=make_backtest_result(),
            strategy_research_result=strategy_research_result,
        )
    )

    assert result.successful is True
    assert result.report is not None
    assert result.report.signals.research_error_count == 1


def test_mismatched_strategy_research_result_symbol_fails_with_clear_error() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-symbol-mismatch",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(symbol="ethusdt"),
        )
    )

    assert result.report is None
    assert len(result.errors) == 1
    assert "symbol" in result.errors[0].message.lower()


def test_mismatched_strategy_research_result_market_fails_with_clear_error() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-market-mismatch",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(market="futures"),
        )
    )

    assert result.report is None
    assert len(result.errors) == 1
    assert "market" in result.errors[0].message.lower()


def test_mismatched_strategy_research_result_timeframe_fails_with_clear_error() -> None:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-timeframe-mismatch",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(timeframe=Timeframe.HOUR_1),
        )
    )

    assert result.report is None
    assert len(result.errors) == 1
    assert "timeframe" in result.errors[0].message.lower()


def test_generate_does_not_run_a_backtest(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_execute(self: OfflineBacktestingService, request: object) -> BacktestRunSummary:
        raise AssertionError("backtest execution should not be called")

    monkeypatch.setattr(OfflineBacktestingService, "execute", fail_execute)
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-no-backtest",
            backtest_result=make_backtest_result(),
        )
    )

    assert result.successful is True
    assert not isinstance(result, BacktestRunSummary)


def test_generate_does_not_call_a_strategy_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_execute(
        self: OfflineStrategyResearchService,
        request: object,
    ) -> StrategyResearchResult:
        raise AssertionError("strategy research execution should not be called")

    monkeypatch.setattr(OfflineStrategyResearchService, "execute", fail_execute)
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-no-provider-call",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(),
        )
    )

    assert result.successful is True
    assert result.report is not None


def test_generate_does_not_write_files(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("file access should not be attempted")

    monkeypatch.setattr("builtins.open", fail_open)
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-no-files",
            backtest_result=make_backtest_result(),
            strategy_research_result=make_strategy_research_result(),
        )
    )

    assert result.successful is True
    assert result.report is not None
    assert builtins_open is not None


def test_output_is_deterministic_for_the_same_input() -> None:
    service = OfflineResearchReportingService()
    request = ResearchReportRequest(
        report_id="b6-deterministic",
        backtest_result=make_backtest_result(),
        strategy_research_result=make_strategy_research_result(),
        title="Deterministic Report",
        notes=("note a", "note b"),
    )

    first_result = service.generate(request)
    second_result = service.generate(request)

    assert first_result == second_result


def test_generated_result_successful_property_works() -> None:
    success_result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id="b6-success",
            backtest_result=make_backtest_result(),
        )
    )
    failure_result = OfflineResearchReportingService().generate(object())

    assert success_result.successful is True
    assert failure_result.successful is False


def test_invalid_request_produces_errors_without_report() -> None:
    result = OfflineResearchReportingService().generate(object())

    assert isinstance(result, ResearchReportGenerationResult)
    assert result.report is None
    assert len(result.errors) == 1
