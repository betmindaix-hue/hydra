from __future__ import annotations

import inspect
from builtins import open as builtins_open
from datetime import UTC, datetime, timedelta

import pytest

import hydra.application.research_run_catalog_service as catalog_service_module
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
from hydra.application.research_run_catalog_dto import (
    ResearchRunCatalogAddResult,
    ResearchRunCatalogError,
    ResearchRunCatalogQuery,
    ResearchRunComparisonSummary,
    ResearchRunRecord,
    ResearchRunStatus,
)
from hydra.application.research_run_catalog_service import InMemoryResearchRunCatalog
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
        source=DataSourceDescriptor(name=f"{symbol}-catalog-series"),
    )


def make_ingestion_result(
    series: MarketDataSeries,
    *,
    dataset_name: str = "catalog-dataset",
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
                message="catalog fixture backtest failure",
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


def make_successful_scenario_result(
    scenario_id: str,
    *,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
    total_return: float = 0.1,
    max_drawdown: float = 0.1,
    trade_count: int = 2,
    signal_count: int = 2,
) -> OfflineResearchScenarioResult:
    series = make_series(symbol=symbol, market=market, timeframe=timeframe)
    strategy_result = make_strategy_result(series)
    backtest_result = make_backtest_result(
        series,
        total_return=total_return,
        max_drawdown=max_drawdown,
        trade_count=trade_count,
        signal_count=signal_count,
    )

    return OfflineResearchScenarioResult(
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


def make_failed_scenario_result(
    scenario_id: str,
    *,
    with_backtest: bool = False,
    symbol: str = "btcusdt",
    market: str = "spot",
    timeframe: Timeframe = Timeframe.MINUTE_1,
    total_return: float = 0.05,
    max_drawdown: float = 0.2,
    trade_count: int = 1,
) -> OfflineResearchScenarioResult:
    if not with_backtest:
        return OfflineResearchScenarioResult(
            scenario_id=scenario_id,
            errors=(
                OfflineResearchScenarioError(
                    stage=OfflineResearchScenarioStage.REPORTING,
                    message="catalog fixture failure",
                    field_name="report",
                ),
            ),
        )

    series = make_series(symbol=symbol, market=market, timeframe=timeframe)
    strategy_result = make_strategy_result(series)
    backtest_result = make_backtest_result(
        series,
        total_return=total_return,
        max_drawdown=max_drawdown,
        trade_count=trade_count,
    )
    return OfflineResearchScenarioResult(
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
                message="catalog fixture failure",
                field_name="report",
            ),
        ),
    )


def test_adds_successful_scenario_result() -> None:
    catalog = InMemoryResearchRunCatalog()

    result = catalog.add_result(make_successful_scenario_result("run-success"))

    assert result.successful is True
    assert result.record is not None
    assert result.record.status is ResearchRunStatus.SUCCESSFUL
    assert result.record.successful is True


def test_adds_failed_scenario_result() -> None:
    catalog = InMemoryResearchRunCatalog()

    result = catalog.add_result(make_failed_scenario_result("run-failure"))

    assert result.successful is True
    assert result.record is not None
    assert result.record.status is ResearchRunStatus.FAILED
    assert result.record.successful is False


def test_duplicate_scenario_id_is_rejected_by_default() -> None:
    catalog = InMemoryResearchRunCatalog()
    scenario_result = make_successful_scenario_result("run-duplicate")

    first_result = catalog.add_result(scenario_result)
    duplicate_result = catalog.add_result(scenario_result)

    assert first_result.successful is True
    assert duplicate_result.successful is False
    assert duplicate_result.record is None
    assert duplicate_result.errors[0].field_name == "scenario_id"


def test_duplicate_scenario_id_is_replaced_when_requested() -> None:
    catalog = InMemoryResearchRunCatalog()
    first_result = catalog.add_result(
        make_successful_scenario_result("run-replace"),
        title="First Title",
    )
    replacement_result = catalog.add_result(
        make_successful_scenario_result("run-replace", total_return=0.3),
        title="Replacement Title",
        replace_existing=True,
    )

    assert first_result.successful is True
    assert replacement_result.successful is True
    assert replacement_result.record is not None
    assert replacement_result.record.title == "Replacement Title"
    assert replacement_result.record.total_return == 0.3
    assert tuple(record.scenario_id for record in catalog.list()) == ("run-replace",)


def test_get_returns_stored_record() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-get"))

    record = catalog.get("run-get")

    assert record is not None
    assert record.scenario_id == "run-get"


def test_get_returns_none_for_missing_scenario_id() -> None:
    assert InMemoryResearchRunCatalog().get("missing-run") is None


def test_list_returns_insertion_order() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-1"))
    catalog.add_result(make_failed_scenario_result("run-2"))
    catalog.add_result(make_successful_scenario_result("run-3"))

    records = catalog.list()

    assert tuple(record.scenario_id for record in records) == ("run-1", "run-2", "run-3")


def test_list_returns_immutable_tuple() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-immutable"))

    records = catalog.list()

    assert isinstance(records, tuple)
    with pytest.raises(TypeError):
        records[0] = records[0]  # type: ignore[index]


def test_list_filters_by_status() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-success"))
    catalog.add_result(make_failed_scenario_result("run-failure"))

    records = catalog.list(ResearchRunCatalogQuery(status=ResearchRunStatus.FAILED))

    assert tuple(record.scenario_id for record in records) == ("run-failure",)


def test_list_filters_by_symbol() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("btc-run", symbol="btcusdt"))
    catalog.add_result(make_successful_scenario_result("eth-run", symbol="ethusdt"))

    records = catalog.list(ResearchRunCatalogQuery(symbol="  btcusdt  "))

    assert tuple(record.scenario_id for record in records) == ("btc-run",)


def test_list_filters_by_market() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("spot-run", market="spot"))
    catalog.add_result(make_successful_scenario_result("futures-run", market="futures"))

    records = catalog.list(ResearchRunCatalogQuery(market=" spot "))

    assert tuple(record.scenario_id for record in records) == ("spot-run",)


def test_list_filters_by_timeframe() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("m1-run", timeframe=Timeframe.MINUTE_1))
    catalog.add_result(make_successful_scenario_result("h1-run", timeframe=Timeframe.HOUR_1))

    records = catalog.list(ResearchRunCatalogQuery(timeframe=" 1m "))

    assert tuple(record.scenario_id for record in records) == ("m1-run",)


def test_list_filters_by_require_report() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("with-report"))
    catalog.add_result(make_failed_scenario_result("without-report", with_backtest=True))

    records = catalog.list(ResearchRunCatalogQuery(require_report=True))

    assert tuple(record.scenario_id for record in records) == ("with-report",)


def test_list_filters_by_require_backtest() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("with-backtest"))
    catalog.add_result(make_failed_scenario_result("also-with-backtest", with_backtest=True))
    catalog.add_result(make_failed_scenario_result("without-backtest"))

    records = catalog.list(ResearchRunCatalogQuery(require_backtest=True))

    assert tuple(record.scenario_id for record in records) == (
        "with-backtest",
        "also-with-backtest",
    )


def test_compare_empty_catalog_returns_zero_counts_and_no_winners() -> None:
    summary = InMemoryResearchRunCatalog().compare()

    assert summary.run_count == 0
    assert summary.successful_run_count == 0
    assert summary.failed_run_count == 0
    assert summary.best_total_return_scenario_id is None
    assert summary.lowest_max_drawdown_scenario_id is None
    assert summary.highest_trade_count_scenario_id is None


def test_compare_counts_successful_and_failed_runs() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("success-a"))
    catalog.add_result(make_failed_scenario_result("failure-a"))

    summary = catalog.compare()

    assert summary.run_count == 2
    assert summary.successful_run_count == 1
    assert summary.failed_run_count == 1


def test_compare_selects_highest_total_return() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-low", total_return=0.1))
    catalog.add_result(make_successful_scenario_result("run-high", total_return=0.4))

    summary = catalog.compare()

    assert summary.best_total_return_scenario_id == "run-high"
    assert summary.best_total_return == 0.4


def test_compare_selects_lowest_max_drawdown() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-wide", max_drawdown=0.3))
    catalog.add_result(make_successful_scenario_result("run-tight", max_drawdown=0.05))

    summary = catalog.compare()

    assert summary.lowest_max_drawdown_scenario_id == "run-tight"
    assert summary.lowest_max_drawdown == 0.05


def test_compare_selects_highest_trade_count() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_successful_scenario_result("run-small", trade_count=1))
    catalog.add_result(make_successful_scenario_result("run-large", trade_count=3))

    summary = catalog.compare()

    assert summary.highest_trade_count_scenario_id == "run-large"
    assert summary.highest_trade_count == 3


def test_compare_uses_earliest_insertion_for_ties() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(
        make_successful_scenario_result(
            "run-first",
            total_return=0.2,
            max_drawdown=0.1,
            trade_count=2,
        )
    )
    catalog.add_result(
        make_successful_scenario_result(
            "run-second",
            total_return=0.2,
            max_drawdown=0.1,
            trade_count=2,
        )
    )

    summary = catalog.compare()

    assert summary.best_total_return_scenario_id == "run-first"
    assert summary.lowest_max_drawdown_scenario_id == "run-first"
    assert summary.highest_trade_count_scenario_id == "run-first"


def test_failed_runs_without_report_or_backtest_do_not_break_comparison() -> None:
    catalog = InMemoryResearchRunCatalog()
    catalog.add_result(make_failed_scenario_result("failed-empty"))
    catalog.add_result(make_successful_scenario_result("successful-run", total_return=0.15))

    summary = catalog.compare()

    assert summary.run_count == 2
    assert summary.failed_run_count == 1
    assert summary.best_total_return_scenario_id == "successful-run"


def test_record_properties_expose_metric_values_from_report_and_backtest() -> None:
    successful_record = ResearchRunRecord(
        scenario_id="successful-run",
        status=ResearchRunStatus.SUCCESSFUL,
        scenario_result=make_successful_scenario_result(
            "successful-run",
            total_return=0.25,
            max_drawdown=0.08,
            trade_count=3,
            signal_count=5,
        ),
    )
    failed_record = ResearchRunRecord(
        scenario_id="failed-run",
        status=ResearchRunStatus.FAILED,
        scenario_result=make_failed_scenario_result(
            "failed-run",
            with_backtest=True,
            total_return=0.05,
            max_drawdown=0.2,
            trade_count=1,
        ),
    )

    assert successful_record.has_report is True
    assert successful_record.has_backtest is True
    assert successful_record.symbol == "BTCUSDT"
    assert successful_record.market == "SPOT"
    assert successful_record.timeframe == "1m"
    assert successful_record.total_return == 0.25
    assert successful_record.max_drawdown == 0.08
    assert successful_record.trade_count == 3
    assert successful_record.signal_count == 5

    assert failed_record.has_report is False
    assert failed_record.has_backtest is True
    assert failed_record.total_return == 0.05
    assert failed_record.max_drawdown == 0.2
    assert failed_record.trade_count == 1
    assert failed_record.signal_count == 2


def test_add_result_rejects_non_scenario_result_input() -> None:
    result = InMemoryResearchRunCatalog().add_result(object())  # type: ignore[arg-type]

    assert result.successful is False
    assert result.record is None
    assert result.errors[0].field_name == "scenario_result"


def test_query_normalizes_string_fields() -> None:
    query = ResearchRunCatalogQuery(
        status=ResearchRunStatus.SUCCESSFUL,
        symbol="  btcusdt  ",
        market="  spot  ",
        timeframe=" 1m ",
        require_report=True,
    )

    assert query.status is ResearchRunStatus.SUCCESSFUL
    assert query.symbol == "BTCUSDT"
    assert query.market == "SPOT"
    assert query.timeframe == "1m"
    assert query.require_report is True


def test_title_and_notes_normalize_correctly() -> None:
    result = InMemoryResearchRunCatalog().add_result(
        make_successful_scenario_result("run-metadata"),
        title="  Catalog Title  ",
        notes=("  note one  ", " ", "note two"),
    )

    assert result.record is not None
    assert result.record.title == "Catalog Title"
    assert result.record.notes == ("note one", "note two")


def test_no_file_access_is_attempted(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("file access should not be attempted")

    catalog = InMemoryResearchRunCatalog()
    monkeypatch.setattr("builtins.open", fail_open)

    add_result = catalog.add_result(make_successful_scenario_result("run-no-open"))
    assert add_result.successful is True
    assert catalog.get("run-no-open") is not None
    assert len(catalog.list()) == 1
    assert catalog.compare().run_count == 1
    assert builtins_open is not None


def test_no_wall_clock_behavior_is_required() -> None:
    source = inspect.getsource(catalog_service_module)

    assert ".now(" not in source
    assert "utcnow(" not in source
    assert ".today(" not in source


def test_independent_catalog_instances_do_not_share_state() -> None:
    first_catalog = InMemoryResearchRunCatalog()
    second_catalog = InMemoryResearchRunCatalog()
    first_catalog.add_result(make_successful_scenario_result("run-shared"))

    assert first_catalog.get("run-shared") is not None
    assert second_catalog.get("run-shared") is None
    assert second_catalog.compare().run_count == 0


def test_record_rejects_mismatched_status_and_scenario_id() -> None:
    successful_result = make_successful_scenario_result("run-record")

    with pytest.raises(ValueError, match="must match OfflineResearchScenarioResult success state"):
        ResearchRunRecord(
            scenario_id="run-record",
            status=ResearchRunStatus.FAILED,
            scenario_result=successful_result,
        )

    with pytest.raises(ValueError, match="must match OfflineResearchScenarioResult scenario_id"):
        ResearchRunRecord(
            scenario_id="different-id",
            status=ResearchRunStatus.SUCCESSFUL,
            scenario_result=successful_result,
        )


def test_catalog_error_and_add_result_validate_invariants() -> None:
    error = ResearchRunCatalogError(
        message="  duplicate run  ",
        field_name="  scenario_id  ",
        scenario_id="  run-duplicate  ",
    )

    assert error.message == "duplicate run"
    assert error.field_name == "scenario_id"
    assert error.scenario_id == "run-duplicate"

    with pytest.raises(ValueError, match="cannot contain both a record and errors"):
        ResearchRunCatalogAddResult(
            record=ResearchRunRecord(
                scenario_id="run-add-result",
                status=ResearchRunStatus.FAILED,
                scenario_result=make_failed_scenario_result("run-add-result"),
            ),
            errors=(ResearchRunCatalogError(message="conflict"),),
        )


def test_query_rejects_non_bool_flags() -> None:
    with pytest.raises(ValueError, match="require_report must be a bool"):
        ResearchRunCatalogQuery(require_report=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="require_backtest must be a bool"):
        ResearchRunCatalogQuery(require_backtest="yes")  # type: ignore[arg-type]


def test_comparison_summary_rejects_inconsistent_counts_and_metric_pairs() -> None:
    with pytest.raises(ValueError, match="must add up to run_count"):
        ResearchRunComparisonSummary(
            run_count=2,
            successful_run_count=1,
            failed_run_count=0,
        )

    with pytest.raises(ValueError, match="must both be provided together"):
        ResearchRunComparisonSummary(
            run_count=1,
            successful_run_count=1,
            failed_run_count=0,
            best_total_return_scenario_id="run-a",
        )
