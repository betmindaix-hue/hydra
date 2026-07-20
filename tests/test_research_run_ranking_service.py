from __future__ import annotations

import inspect
from builtins import open as builtins_open
from datetime import UTC, datetime, timedelta

import pytest

import hydra.application.research_run_ranking_service as ranking_service_module
from hydra.application.backtesting_dto import BacktestRunSummary, BacktestValidationError
from hydra.application.market_data_ingestion_dto import OfflineDatasetIngestionResult
from hydra.application.offline_research_scenario_dto import (
    OfflineResearchScenarioError,
    OfflineResearchScenarioResult,
    OfflineResearchScenarioStage,
)
from hydra.application.research_reporting_dto import (
    ResearchReportGenerationError,
    ResearchReportGenerationResult,
    ResearchReportRequest,
)
from hydra.application.research_reporting_service import OfflineResearchReportingService
from hydra.application.research_run_catalog_dto import ResearchRunRecord, ResearchRunStatus
from hydra.application.research_run_ranking_dto import (
    ResearchRunEligibilityCriteria,
    ResearchRunExclusionReason,
    ResearchRunRankingDirection,
    ResearchRunRankingEntry,
    ResearchRunRankingMetric,
    ResearchRunRankingResult,
    ResearchRunRankingSpec,
)
from hydra.application.research_run_ranking_service import ResearchRunRankingService
from hydra.application.strategy_research_dto import StrategyResearchError, StrategyResearchResult
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
    bars = tuple(
        OHLCVBar(
            symbol=Symbol(symbol),
            market=Market(market),
            timeframe=timeframe,
            timestamp=datetime(2026, 7, 20, 9, 0, tzinfo=UTC) + timedelta(minutes=index),
            open_price=100 + index,
            high_price=101 + index,
            low_price=99 + index,
            close_price=100 + index,
            volume=10 + index,
        )
        for index in range(3)
    )

    return MarketDataSeries(
        symbol=Symbol(symbol),
        market=Market(market),
        timeframe=timeframe,
        bars=bars,
        source=DataSourceDescriptor(name=f"{symbol}-ranking-series"),
    )


def make_ingestion_result(
    series: MarketDataSeries,
    *,
    dataset_name: str = "ranking-dataset",
) -> OfflineDatasetIngestionResult:
    return OfflineDatasetIngestionResult(
        dataset_name=dataset_name,
        source=series.source or DataSourceDescriptor(name=dataset_name),
        series=(series,),
        processed_record_count=series.bar_count,
        accepted_record_count=series.bar_count,
        rejected_record_count=0,
    )


def make_strategy_result(
    series: MarketDataSeries,
    *,
    errors: tuple[StrategyResearchError, ...] = (),
    rejected_signal_count: int = 0,
) -> StrategyResearchResult:
    time_range = BacktestTimeRange(
        start=series.bars[0].timestamp,
        end=series.bars[-1].timestamp,
    )
    signals = (
        ResearchSignal(
            timestamp=series.bars[0].timestamp,
            direction=BacktestDirection.BUY,
        ),
        ResearchSignal(
            timestamp=series.bars[-1].timestamp,
            direction=BacktestDirection.SELL,
        ),
    )

    return StrategyResearchResult(
        research_id=f"{series.symbol.value}-research",
        market_data_series=series,
        time_range=time_range,
        signals=signals,
        errors=errors,
        selected_bar_count=series.bar_count,
        rejected_signal_count=rejected_signal_count,
    )


def make_trades(series: MarketDataSeries, trade_count: int) -> tuple[SimulatedTrade, ...]:
    trades: list[SimulatedTrade] = []
    for index in range(trade_count):
        direction = BacktestDirection.BUY if index % 2 == 0 else BacktestDirection.SELL
        trades.append(
            SimulatedTrade(
                timestamp=series.bars[min(index, len(series.bars) - 1)].timestamp,
                direction=direction,
                quantity=1,
                price=100 + index,
            )
        )
    return tuple(trades)


def make_backtest_result(
    series: MarketDataSeries,
    *,
    total_return: float = 0.1,
    max_drawdown: float = 0.1,
    trade_count: int = 2,
    signal_count: int = 2,
) -> BacktestResult:
    simulated_trades = make_trades(series, trade_count)
    final_position = (
        SimulatedPosition(
            quantity=1,
            average_entry_price=100,
            opened_at=series.bars[-1].timestamp,
        )
        if trade_count % 2 == 1
        else SimulatedPosition()
    )

    return BacktestResult(
        backtest_id=BacktestId(f"{series.symbol.value.lower()}-backtest"),
        symbol=series.symbol,
        market=series.market,
        timeframe=series.timeframe,
        time_range=BacktestTimeRange(
            start=series.bars[0].timestamp,
            end=series.bars[-1].timestamp,
        ),
        source=series.source,
        simulated_trades=simulated_trades,
        equity_curve=(
            EquityCurvePoint(
                timestamp=series.bars[0].timestamp,
                equity=1000,
                cash=1000,
                position_quantity=0,
            ),
            EquityCurvePoint(
                timestamp=series.bars[1].timestamp,
                equity=900,
                cash=900 if trade_count % 2 == 0 else 0,
                position_quantity=0 if trade_count % 2 == 0 else 1,
            ),
            EquityCurvePoint(
                timestamp=series.bars[2].timestamp,
                equity=1000 + (1000 * total_return),
                cash=1000 if trade_count % 2 == 0 else 0,
                position_quantity=0 if trade_count % 2 == 0 else 1,
            ),
        ),
        metrics=BacktestMetrics(
            initial_cash=1000,
            ending_cash=1000 if trade_count % 2 == 0 else 0,
            ending_equity=1000 + (1000 * total_return),
            total_return=total_return,
            max_drawdown=max_drawdown,
            trade_count=trade_count,
        ),
        final_position=final_position,
        signal_count=signal_count,
    )


def make_backtest_summary(
    backtest_result: BacktestResult,
    *,
    failed: bool = False,
) -> BacktestRunSummary:
    errors = (
        (
            BacktestValidationError(
                message="ranking fixture backtest failure",
                field_name="backtest",
            ),
        )
        if failed
        else ()
    )
    return BacktestRunSummary(
        backtest_id=backtest_result.backtest_id.value,
        result=backtest_result,
        errors=errors,
        processed_bar_count=len(backtest_result.equity_curve),
        simulated_trade_count=len(backtest_result.simulated_trades),
        ignored_signal_count=0,
    )


def make_report_result(
    backtest_result: BacktestResult,
    strategy_result: StrategyResearchResult,
    *,
    report_id: str,
) -> ResearchReportGenerationResult:
    result = OfflineResearchReportingService().generate(
        ResearchReportRequest(
            report_id=report_id,
            backtest_result=backtest_result,
            strategy_research_result=strategy_result,
        )
    )
    assert result.report is not None
    return result


def make_successful_record(
    scenario_id: str,
    *,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
    total_return: float = 0.1,
    max_drawdown: float = 0.1,
    trade_count: int = 2,
    signal_count: int = 2,
) -> ResearchRunRecord:
    series = make_series(symbol=symbol, market=market, timeframe=timeframe)
    strategy_result = make_strategy_result(series)
    backtest_result = make_backtest_result(
        series,
        total_return=total_return,
        max_drawdown=max_drawdown,
        trade_count=trade_count,
        signal_count=signal_count,
    )
    scenario_result = OfflineResearchScenarioResult(
        scenario_id=scenario_id,
        ingestion_result=make_ingestion_result(series, dataset_name=f"{scenario_id}-dataset"),
        strategy_research_result=strategy_result,
        backtest_summary=make_backtest_summary(backtest_result),
        report_generation_result=make_report_result(
            backtest_result,
            strategy_result,
            report_id=f"{scenario_id}-report",
        ),
    )
    return ResearchRunRecord(
        scenario_id=scenario_id,
        status=ResearchRunStatus.SUCCESSFUL,
        scenario_result=scenario_result,
    )


def make_failed_record(
    scenario_id: str,
    *,
    with_backtest: bool = False,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
    total_return: float = 0.05,
    max_drawdown: float = 0.2,
    trade_count: int = 1,
    signal_count: int = 2,
) -> ResearchRunRecord:
    if not with_backtest:
        scenario_result = OfflineResearchScenarioResult(
            scenario_id=scenario_id,
            errors=(
                OfflineResearchScenarioError(
                    stage=OfflineResearchScenarioStage.REPORTING,
                    message="ranking fixture failure",
                    field_name="report",
                ),
            ),
        )
        return ResearchRunRecord(
            scenario_id=scenario_id,
            status=ResearchRunStatus.FAILED,
            scenario_result=scenario_result,
        )

    series = make_series(symbol=symbol, market=market, timeframe=timeframe)
    strategy_result = make_strategy_result(series)
    backtest_result = make_backtest_result(
        series,
        total_return=total_return,
        max_drawdown=max_drawdown,
        trade_count=trade_count,
        signal_count=signal_count,
    )
    scenario_result = OfflineResearchScenarioResult(
        scenario_id=scenario_id,
        ingestion_result=make_ingestion_result(series, dataset_name=f"{scenario_id}-dataset"),
        strategy_research_result=strategy_result,
        backtest_summary=make_backtest_summary(backtest_result, failed=True),
        report_generation_result=ResearchReportGenerationResult(
            errors=(ResearchReportGenerationError(message="report unavailable"),)
        ),
        errors=(
            OfflineResearchScenarioError(
                stage=OfflineResearchScenarioStage.REPORTING,
                message="ranking fixture failure",
                field_name="report",
            ),
        ),
    )
    return ResearchRunRecord(
        scenario_id=scenario_id,
        status=ResearchRunStatus.FAILED,
        scenario_result=scenario_result,
    )


def test_ranks_by_total_return_higher_first_by_default() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-low", total_return=0.1),
            make_successful_record("run-high", total_return=0.4),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-high", "run-low")


def test_ranks_by_max_drawdown_lower_first_by_default() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-wide", max_drawdown=0.3),
            make_successful_record("run-tight", max_drawdown=0.05),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.MAX_DRAWDOWN),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-tight", "run-wide")


def test_ranks_by_trade_count_higher_first_by_default() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-small", trade_count=1),
            make_successful_record("run-large", trade_count=4),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TRADE_COUNT),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-large", "run-small")


def test_ranks_by_signal_count_higher_first_by_default() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-few", signal_count=2),
            make_successful_record("run-many", signal_count=5),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.SIGNAL_COUNT),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-many", "run-few")


def test_explicit_higher_first_works() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-low", max_drawdown=0.05),
            make_successful_record("run-high", max_drawdown=0.3),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.MAX_DRAWDOWN,
            direction=ResearchRunRankingDirection.HIGHER_FIRST,
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-high", "run-low")


def test_explicit_lower_first_works() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-low", total_return=0.1),
            make_successful_record("run-high", total_return=0.4),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            direction=ResearchRunRankingDirection.LOWER_FIRST,
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-low", "run-high")


def test_tie_breaks_by_earliest_input_order() -> None:
    service = ResearchRunRankingService()
    records = (
        make_successful_record("run-first", total_return=0.2),
        make_successful_record("run-second", total_return=0.2),
    )

    result = service.rank(
        records,
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-first", "run-second")
    assert tuple(entry.insertion_index for entry in result.entries) == (0, 1)


def test_rank_numbers_are_sequential_from_one() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-c", total_return=0.2),
            make_successful_record("run-a", total_return=0.4),
            make_successful_record("run-b", total_return=0.3),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert tuple(entry.rank for entry in result.entries) == (1, 2, 3)


def test_select_best_returns_top_entry() -> None:
    top = ResearchRunRankingService().select_best(
        (
            make_successful_record("run-a", total_return=0.1),
            make_successful_record("run-b", total_return=0.5),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert top is not None
    assert top.scenario_id == "run-b"


def test_select_best_returns_none_when_no_eligible_entries_exist() -> None:
    top = ResearchRunRankingService().select_best(
        (make_failed_record("run-failed"),),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert top is None


def test_default_criteria_excludes_failed_runs() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-success", total_return=0.2),
            make_failed_record("run-failed", with_backtest=True, total_return=0.4),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-success",)
    assert result.excluded[0].scenario_id == "run-failed"
    assert result.excluded[0].reason == "status mismatch"


def test_criteria_can_include_failed_runs_when_status_is_none() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-success", total_return=0.2),
            make_failed_record("run-failed", with_backtest=True, total_return=0.4),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(status=None),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-failed", "run-success")


def test_filters_by_symbol() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-btc", symbol="btcusdt"),
            make_successful_record("run-eth", symbol="ethusdt"),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(symbol="  btcusdt  "),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-btc",)
    assert result.excluded[0].reason == "symbol mismatch"


def test_filters_by_market() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-spot", market="spot"),
            make_successful_record("run-futures", market="futures"),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(market=" spot "),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-spot",)
    assert result.excluded[0].reason == "market mismatch"


def test_filters_by_timeframe() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-m1", timeframe=Timeframe.MINUTE_1),
            make_successful_record("run-h1", timeframe=Timeframe.HOUR_1),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(timeframe=" 1m "),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-m1",)
    assert result.excluded[0].reason == "timeframe mismatch"


def test_require_report_excludes_records_without_reports() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-report"),
            make_failed_record("run-no-report", with_backtest=True),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(
                status=None,
                require_report=True,
            ),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-report",)
    assert result.excluded[0].reason == "missing report"


def test_require_backtest_excludes_records_without_backtest() -> None:
    service = ResearchRunRankingService()
    result = service.rank(
        (
            make_successful_record("run-backtest"),
            make_failed_record("run-no-backtest"),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(
                status=None,
                require_backtest=True,
            ),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-backtest",)
    assert result.excluded[0].reason == "missing backtest"


def test_min_total_return_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", total_return=0.1),
            make_successful_record("run-high", total_return=0.4),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(min_total_return=0.2),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-high",)
    assert result.excluded[0].reason == "below minimum threshold"


def test_max_total_return_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", total_return=0.1),
            make_successful_record("run-high", total_return=0.4),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(max_total_return=0.2),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-low",)
    assert result.excluded[0].reason == "above maximum threshold"


def test_min_max_drawdown_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", max_drawdown=0.05),
            make_successful_record("run-high", max_drawdown=0.2),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.MAX_DRAWDOWN,
            eligibility=ResearchRunEligibilityCriteria(min_max_drawdown=0.1),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-high",)
    assert result.excluded[0].reason == "below minimum threshold"


def test_max_max_drawdown_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", max_drawdown=0.05),
            make_successful_record("run-high", max_drawdown=0.2),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.MAX_DRAWDOWN,
            eligibility=ResearchRunEligibilityCriteria(max_max_drawdown=0.1),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-low",)
    assert result.excluded[0].reason == "above maximum threshold"


def test_min_trade_count_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", trade_count=1),
            make_successful_record("run-high", trade_count=3),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TRADE_COUNT,
            eligibility=ResearchRunEligibilityCriteria(min_trade_count=2),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-high",)
    assert result.excluded[0].reason == "below minimum threshold"


def test_max_trade_count_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", trade_count=1),
            make_successful_record("run-high", trade_count=3),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TRADE_COUNT,
            eligibility=ResearchRunEligibilityCriteria(max_trade_count=2),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-low",)
    assert result.excluded[0].reason == "above maximum threshold"


def test_min_signal_count_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", signal_count=1),
            make_successful_record("run-high", signal_count=4),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.SIGNAL_COUNT,
            eligibility=ResearchRunEligibilityCriteria(min_signal_count=2),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-high",)
    assert result.excluded[0].reason == "below minimum threshold"


def test_max_signal_count_filter_works() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-low", signal_count=1),
            make_successful_record("run-high", signal_count=4),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.SIGNAL_COUNT,
            eligibility=ResearchRunEligibilityCriteria(max_signal_count=2),
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-low",)
    assert result.excluded[0].reason == "above maximum threshold"


def test_missing_metric_is_excluded_with_a_stable_reason() -> None:
    result = ResearchRunRankingService().rank(
        (make_failed_record("run-missing"),),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            eligibility=ResearchRunEligibilityCriteria(status=None),
        ),
    )

    assert result.entries == ()
    assert result.excluded == (
        ResearchRunExclusionReason(
            scenario_id="run-missing",
            reason="missing metric",
            field_name="total_return",
        ),
    )


def test_limit_returns_only_top_n_entries() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-a", total_return=0.1),
            make_successful_record("run-b", total_return=0.3),
            make_successful_record("run-c", total_return=0.2),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            limit=2,
        ),
    )

    assert tuple(entry.scenario_id for entry in result.entries) == ("run-b", "run-c")


def test_limit_does_not_change_considered_count() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-a", total_return=0.1),
            make_successful_record("run-b", total_return=0.3),
            make_successful_record("run-c", total_return=0.2),
        ),
        ResearchRunRankingSpec(
            metric=ResearchRunRankingMetric.TOTAL_RETURN,
            limit=2,
        ),
    )

    assert result.considered_count == 3
    assert len(result.entries) == 2


def test_result_top_exposes_first_ranked_entry() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-a", total_return=0.1),
            make_successful_record("run-b", total_return=0.2),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert result.top is not None
    assert result.top.scenario_id == "run-b"


def test_result_selected_scenario_id_exposes_top_scenario_id() -> None:
    result = ResearchRunRankingService().rank(
        (
            make_successful_record("run-a", total_return=0.1),
            make_successful_record("run-b", total_return=0.2),
        ),
        ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
    )

    assert result.selected_scenario_id == "run-b"


def test_invalid_spec_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="spec must be a ResearchRunRankingSpec"):
        ResearchRunRankingService().rank(
            (make_successful_record("run-a"),),
            object(),  # type: ignore[arg-type]
        )


def test_non_record_item_is_handled_deterministically() -> None:
    with pytest.raises(ValueError, match="must contain only ResearchRunRecord values"):
        ResearchRunRankingService().rank(
            (make_successful_record("run-a"), object()),  # type: ignore[arg-type]
            ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
        )


def test_string_records_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be an iterable of ResearchRunRecord values"):
        ResearchRunRankingService().rank(
            "not-records",  # type: ignore[arg-type]
            ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN),
        )


def test_criteria_validates_minimum_is_not_greater_than_maximum() -> None:
    with pytest.raises(ValueError, match="minimum cannot exceed maximum"):
        ResearchRunEligibilityCriteria(min_total_return=0.5, max_total_return=0.2)


def test_bool_numeric_thresholds_are_rejected() -> None:
    with pytest.raises(ValueError, match="min_total_return must be a number"):
        ResearchRunEligibilityCriteria(min_total_return=True)

    with pytest.raises(ValueError, match="max_trade_count must be an integer"):
        ResearchRunEligibilityCriteria(max_trade_count=False)


def test_ranking_result_rejects_duplicate_entry_scenario_ids() -> None:
    record = make_successful_record("run-duplicate")

    with pytest.raises(ValueError, match="duplicate scenario IDs"):
        ResearchRunRankingResult(
            entries=(
                ResearchRunRankingEntry(
                    rank=1,
                    scenario_id="run-duplicate",
                    record=record,
                    metric=ResearchRunRankingMetric.TOTAL_RETURN,
                    metric_value=record.total_return or 0.0,
                    insertion_index=0,
                ),
                ResearchRunRankingEntry(
                    rank=2,
                    scenario_id="run-duplicate",
                    record=record,
                    metric=ResearchRunRankingMetric.TOTAL_RETURN,
                    metric_value=record.total_return or 0.0,
                    insertion_index=1,
                ),
            ),
            considered_count=2,
        )


def test_two_service_instances_share_no_mutable_state() -> None:
    first_service = ResearchRunRankingService()
    second_service = ResearchRunRankingService()
    spec = ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN)

    first_top = first_service.select_best(
        (
            make_successful_record("run-a", total_return=0.1),
            make_successful_record("run-b", total_return=0.3),
        ),
        spec,
    )
    second_top = second_service.select_best(
        (
            make_successful_record("run-c", total_return=0.2),
            make_successful_record("run-d", total_return=0.4),
        ),
        spec,
    )

    assert first_top is not None
    assert second_top is not None
    assert first_top.scenario_id == "run-b"
    assert second_top.scenario_id == "run-d"


def test_no_wall_clock_behavior_is_required() -> None:
    source = inspect.getsource(ranking_service_module)

    assert ".now(" not in source
    assert "utcnow(" not in source
    assert ".today(" not in source


def test_no_file_access_is_attempted(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("file access should not be attempted")

    monkeypatch.setattr("builtins.open", fail_open)
    records = (
        make_successful_record("run-a", total_return=0.1),
        make_successful_record("run-b", total_return=0.2),
    )
    spec = ResearchRunRankingSpec(metric=ResearchRunRankingMetric.TOTAL_RETURN)

    result = ResearchRunRankingService().rank(records, spec)
    top = ResearchRunRankingService().select_best(records, spec)

    assert result.top is not None
    assert top is not None
    assert builtins_open is not None
