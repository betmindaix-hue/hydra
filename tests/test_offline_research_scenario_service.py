from __future__ import annotations

from builtins import open as builtins_open
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from hydra.adapters.strategy_research import (
    DeterministicFixtureStrategyResearchProvider,
    FixtureSignalInstruction,
)
from hydra.application.backtesting_dto import (
    BacktestRequest,
    BacktestRunSummary,
    BacktestValidationError,
)
from hydra.application.backtesting_service import OfflineBacktestingService
from hydra.application.market_data_ingestion_dto import (
    OfflineDatasetIngestionError,
    OfflineDatasetIngestionRequest,
    OfflineDatasetIngestionResult,
    OfflineMarketDataRecord,
)
from hydra.application.offline_research_scenario_dto import (
    OfflineResearchScenarioError,
    OfflineResearchScenarioRequest,
    OfflineResearchScenarioResult,
    OfflineResearchScenarioStage,
)
from hydra.application.offline_research_scenario_service import OfflineResearchScenarioService
from hydra.application.research_reporting_dto import (
    ResearchReportGenerationError,
    ResearchReportGenerationResult,
    ResearchReportRequest,
)
from hydra.application.research_reporting_service import OfflineResearchReportingService
from hydra.application.strategy_research_dto import StrategyResearchRequest
from hydra.domain.backtesting import BacktestDirection, ResearchSignal
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_record(index: int, close_price: float = 100.0) -> OfflineMarketDataRecord:
    timestamp = datetime(2026, 7, 19, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    open_price = close_price - 1
    return OfflineMarketDataRecord(
        symbol="btcusdt",
        market="spot",
        timeframe="1m",
        timestamp=timestamp,
        open_price=open_price,
        high_price=close_price + 1,
        low_price=open_price - 1,
        close_price=close_price,
        volume=10 + index,
    )


def make_series(
    *close_prices: float,
    symbol: str = "btcusdt",
) -> MarketDataSeries:
    bars = tuple(
        OHLCVBar(
            symbol=Symbol(symbol),
            market=Market("spot"),
            timeframe=Timeframe.MINUTE_1,
            timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=UTC) + timedelta(minutes=index),
            open_price=close_price - 1,
            high_price=close_price + 1,
            low_price=close_price - 2,
            close_price=close_price,
            volume=10 + index,
        )
        for index, close_price in enumerate(close_prices)
    )
    return MarketDataSeries(
        symbol=Symbol(symbol),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=bars,
        source=DataSourceDescriptor(name="scenario-fixture-series"),
    )


def make_request(**overrides: object) -> OfflineResearchScenarioRequest:
    payload: dict[str, Any] = {
        "scenario_id": "b7-scenario",
        "dataset_name": "btc-fixture-dataset",
        "records": (
            make_record(0, close_price=100.0),
            make_record(1, close_price=110.0),
            make_record(2, close_price=120.0),
        ),
        "strategy_provider": DeterministicFixtureStrategyResearchProvider(
            instructions=(
                FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.BUY),
                FixtureSignalInstruction(bar_index=2, direction=BacktestDirection.SELL),
            )
        ),
        "research_id": "b7-research",
        "backtest_id": "b7-backtest",
        "report_id": "b7-report",
        "initial_cash": 1000.0,
        "title": "Deterministic offline scenario",
        "notes": ("baseline note",),
    }
    payload.update(overrides)
    return OfflineResearchScenarioRequest(**payload)


class TrackingStrategyProvider:
    def __init__(self, order_log: list[str]) -> None:
        self._order_log = order_log
        self._delegate = DeterministicFixtureStrategyResearchProvider(
            instructions=(
                FixtureSignalInstruction(bar_index=0, direction=BacktestDirection.BUY),
                FixtureSignalInstruction(bar_index=2, direction=BacktestDirection.SELL),
            )
        )
        self.calls = 0

    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        self.calls += 1
        self._order_log.append("strategy")
        return self._delegate.generate_signals(request)


class CountingStrategyProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        self.calls += 1
        return ()


class OutOfRangeSignalProvider:
    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        return (
            ResearchSignal(
                timestamp=datetime(2026, 7, 19, 13, 0, tzinfo=UTC),
                direction=BacktestDirection.BUY,
            ),
        )


class ExplodingStrategyProvider:
    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        raise RuntimeError("fixture provider exploded")


class StaticIngestionService:
    def __init__(self, result: OfflineDatasetIngestionResult) -> None:
        self._result = result
        self.calls = 0

    def execute(self, request: OfflineDatasetIngestionRequest) -> OfflineDatasetIngestionResult:
        self.calls += 1
        return self._result


class TrackingBacktestingService:
    def __init__(self, order_log: list[str]) -> None:
        self._delegate = OfflineBacktestingService()
        self._order_log = order_log
        self.calls = 0

    def execute(self, request: BacktestRequest) -> BacktestRunSummary:
        self.calls += 1
        self._order_log.append("backtest")
        return self._delegate.execute(request)


class StaticBacktestingService:
    def __init__(self, summary: BacktestRunSummary) -> None:
        self._summary = summary
        self.calls = 0

    def execute(self, request: BacktestRequest) -> BacktestRunSummary:
        self.calls += 1
        return self._summary


class TrackingReportingService:
    def __init__(self, order_log: list[str]) -> None:
        self._delegate = OfflineResearchReportingService()
        self._order_log = order_log
        self.calls = 0

    def generate(self, request: ResearchReportRequest) -> ResearchReportGenerationResult:
        self.calls += 1
        self._order_log.append("report")
        return self._delegate.generate(request)


class StaticReportingService:
    def __init__(self, result: ResearchReportGenerationResult) -> None:
        self._result = result
        self.calls = 0

    def generate(self, request: ResearchReportRequest) -> ResearchReportGenerationResult:
        self.calls += 1
        return self._result


def test_executes_deterministic_end_to_end_offline_research_scenario(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("file access should not be attempted")

    call_order: list[str] = []
    provider = TrackingStrategyProvider(call_order)
    backtesting_service = TrackingBacktestingService(call_order)
    reporting_service = TrackingReportingService(call_order)
    service = OfflineResearchScenarioService(
        backtesting_service=backtesting_service,
        reporting_service=reporting_service,
    )
    request = make_request(strategy_provider=provider)
    monkeypatch.setattr("builtins.open", fail_open)

    result = service.execute(request)

    assert result.successful is True
    assert result.ingestion_result is not None
    assert result.ingestion_result.is_successful is True
    assert len(result.ingestion_result.series) == 1
    assert result.strategy_research_result is not None
    assert result.strategy_research_result.successful is True
    assert tuple(signal.direction for signal in result.strategy_research_result.signals) == (
        BacktestDirection.BUY,
        BacktestDirection.SELL,
    )
    assert result.backtest_summary is not None
    assert result.backtest_summary.successful is True
    assert result.backtest_summary.result is not None
    assert result.backtest_summary.simulated_trade_count == 2
    assert result.report_generation_result is not None
    assert result.report_generation_result.successful is True
    assert result.report_generation_result.report is not None
    assert call_order == ["strategy", "backtest", "report"]
    assert provider.calls == 1
    assert backtesting_service.calls == 1
    assert reporting_service.calls == 1
    assert builtins_open is not None

    report = result.report_generation_result.report
    backtest_result = result.backtest_summary.result
    assert backtest_result.metrics is not None
    assert report.metrics.initial_cash == backtest_result.metrics.initial_cash
    assert report.metrics.ending_cash == backtest_result.metrics.ending_cash
    assert report.metrics.total_return == backtest_result.metrics.total_return
    assert report.metrics.trade_count == backtest_result.metrics.trade_count
    assert report.signals.research_signal_count == 2
    assert report.signals.buy_signal_count == 1
    assert report.signals.sell_signal_count == 1
    assert report.simulated_trades.buy_count == 1
    assert report.simulated_trades.sell_count == 1
    assert report.risk.max_drawdown == backtest_result.metrics.max_drawdown


def test_repeated_execution_with_same_request_returns_equal_results() -> None:
    service = OfflineResearchScenarioService()
    request = make_request()

    first_result = service.execute(request)
    second_result = service.execute(request)

    assert first_result == second_result


def test_rejects_non_request_input_with_scenario_error() -> None:
    result = OfflineResearchScenarioService().execute(object())

    assert isinstance(result, OfflineResearchScenarioResult)
    assert result.successful is False
    assert len(result.errors) == 1
    assert result.errors[0].stage is OfflineResearchScenarioStage.INGESTION
    assert result.errors[0].field_name == "request"


def test_ingestion_failure_stops_before_strategy_research() -> None:
    provider = CountingStrategyProvider()
    ingestion_result = OfflineDatasetIngestionResult(
        dataset_name="btc-fixture-dataset",
        source=DataSourceDescriptor(name="failed-ingestion"),
        errors=(
            OfflineDatasetIngestionError(
                dataset_name="btc-fixture-dataset",
                message="timestamp must be timezone-aware",
                field_name="timestamp",
            ),
        ),
        processed_record_count=1,
        accepted_record_count=0,
        rejected_record_count=1,
    )
    service = OfflineResearchScenarioService(
        ingestion_service=StaticIngestionService(ingestion_result),
    )

    result = service.execute(make_request(strategy_provider=provider))

    assert result.successful is False
    assert result.strategy_research_result is None
    assert result.backtest_summary is None
    assert result.report_generation_result is None
    assert result.errors[0].stage is OfflineResearchScenarioStage.INGESTION
    assert provider.calls == 0


def test_ingestion_returning_zero_series_stops_before_strategy_research() -> None:
    provider = CountingStrategyProvider()
    ingestion_result = OfflineDatasetIngestionResult(
        dataset_name="btc-fixture-dataset",
        source=DataSourceDescriptor(name="empty-ingestion"),
        processed_record_count=0,
        accepted_record_count=0,
        rejected_record_count=0,
    )
    service = OfflineResearchScenarioService(
        ingestion_service=StaticIngestionService(ingestion_result),
    )

    result = service.execute(make_request(strategy_provider=provider))

    assert result.successful is False
    assert result.errors[0].stage is OfflineResearchScenarioStage.INGESTION
    assert "did not produce" in result.errors[0].message
    assert provider.calls == 0


def test_ingestion_returning_multiple_series_stops_before_strategy_research() -> None:
    provider = CountingStrategyProvider()
    first_series = make_series(100.0)
    second_series = make_series(200.0, symbol="ethusdt")
    ingestion_result = OfflineDatasetIngestionResult(
        dataset_name="btc-fixture-dataset",
        source=DataSourceDescriptor(name="mixed-ingestion"),
        series=(first_series, second_series),
        processed_record_count=2,
        accepted_record_count=2,
        rejected_record_count=0,
    )
    service = OfflineResearchScenarioService(
        ingestion_service=StaticIngestionService(ingestion_result),
    )

    result = service.execute(make_request(strategy_provider=provider))

    assert result.successful is False
    assert result.errors[0].stage is OfflineResearchScenarioStage.INGESTION
    assert "exactly one" in result.errors[0].message
    assert provider.calls == 0


def test_strategy_research_failure_stops_before_backtesting() -> None:
    backtesting_service = StaticBacktestingService(
        BacktestRunSummary(
            backtest_id="b7-backtest",
            errors=(
                BacktestValidationError(
                    message="backtesting should not run",
                    field_name="research_signals",
                ),
            ),
        )
    )
    service = OfflineResearchScenarioService(backtesting_service=backtesting_service)

    result = service.execute(make_request(strategy_provider=OutOfRangeSignalProvider()))

    assert result.successful is False
    assert result.strategy_research_result is not None
    assert result.backtest_summary is None
    assert result.report_generation_result is None
    assert result.errors[0].stage is OfflineResearchScenarioStage.STRATEGY_RESEARCH
    assert backtesting_service.calls == 0


def test_backtesting_failure_stops_before_reporting() -> None:
    reporting_service = StaticReportingService(ResearchReportGenerationResult())
    backtesting_service = StaticBacktestingService(
        BacktestRunSummary(
            backtest_id="b7-backtest",
            errors=(
                BacktestValidationError(
                    message="simulated backtesting failure",
                    field_name="research_signals",
                ),
            ),
        )
    )
    service = OfflineResearchScenarioService(
        backtesting_service=backtesting_service,
        reporting_service=reporting_service,
    )

    result = service.execute(make_request())

    assert result.successful is False
    assert result.backtest_summary is not None
    assert result.report_generation_result is None
    assert result.errors[0].stage is OfflineResearchScenarioStage.BACKTESTING
    assert reporting_service.calls == 0


def test_reporting_failure_returns_reporting_stage_error() -> None:
    reporting_service = StaticReportingService(
        ResearchReportGenerationResult(
            errors=(
                ResearchReportGenerationError(
                    message="report rendering is outside scope",
                    field_name="report",
                ),
            )
        )
    )
    service = OfflineResearchScenarioService(reporting_service=reporting_service)

    result = service.execute(make_request())

    assert result.successful is False
    assert result.report_generation_result is not None
    assert result.errors[0].stage is OfflineResearchScenarioStage.REPORTING
    assert "outside scope" in result.errors[0].message


def test_provider_error_is_reported_as_strategy_research_failure() -> None:
    service = OfflineResearchScenarioService()

    result = service.execute(make_request(strategy_provider=ExplodingStrategyProvider()))

    assert result.successful is False
    assert result.strategy_research_result is not None
    assert result.errors[0].stage is OfflineResearchScenarioStage.STRATEGY_RESEARCH
    assert "fixture provider exploded" in result.errors[0].message


def test_request_rejects_invalid_initial_cash() -> None:
    with pytest.raises(ValueError, match="initial_cash must be positive"):
        make_request(initial_cash=0)


@pytest.mark.parametrize(
    "field_name",
    ("scenario_id", "dataset_name", "research_id", "backtest_id", "report_id"),
)
def test_request_rejects_blank_identifiers(field_name: str) -> None:
    with pytest.raises(ValueError, match="non-blank string"):
        make_request(**{field_name: "   "})


@pytest.mark.parametrize("field_name", ("start_timestamp", "end_timestamp"))
def test_request_rejects_naive_timestamps(field_name: str) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        make_request(**{field_name: datetime(2026, 7, 19, 12, 0)})


def test_request_strips_title_and_notes() -> None:
    request = make_request(title="  Scenario Title  ", notes=("  note one  ", " ", "note two"))
    blank_title_request = make_request(title="   ", notes=(" ",))

    assert request.title == "Scenario Title"
    assert request.notes == ("note one", "note two")
    assert blank_title_request.title is None
    assert blank_title_request.notes == ()


def test_request_stores_records_and_notes_immutably() -> None:
    source_records = [make_record(0), make_record(1)]
    source_notes = ["  alpha  ", "beta  "]
    request = make_request(
        records=cast(tuple[OfflineMarketDataRecord, ...], source_records),
        notes=cast(tuple[str, ...], source_notes),
    )
    source_records.append(make_record(2))
    source_notes.append("gamma")

    assert isinstance(request.records, tuple)
    assert isinstance(request.notes, tuple)
    assert len(request.records) == 2
    assert request.notes == ("alpha", "beta")


def test_request_rejects_invalid_record_collections() -> None:
    with pytest.raises(ValueError, match="records must be an iterable"):
        make_request(records="not-records")

    with pytest.raises(ValueError, match="records must not be empty"):
        make_request(records=())

    with pytest.raises(ValueError, match="must contain only OfflineMarketDataRecord"):
        make_request(records=(object(),))


def test_request_rejects_invalid_strategy_provider_and_time_window() -> None:
    with pytest.raises(ValueError, match="must implement StrategyResearchProviderPort"):
        make_request(strategy_provider=object())

    with pytest.raises(ValueError, match="must be before end_timestamp"):
        make_request(
            start_timestamp=datetime(2026, 7, 19, 12, 1, tzinfo=UTC),
            end_timestamp=datetime(2026, 7, 19, 12, 1, tzinfo=UTC),
        )


def test_request_accepts_duck_typed_strategy_provider() -> None:
    provider = CountingStrategyProvider()
    request = make_request(strategy_provider=provider)

    assert request.strategy_provider is provider


def test_scenario_error_normalizes_message_and_field_name() -> None:
    error = OfflineResearchScenarioError(
        stage=OfflineResearchScenarioStage.REPORTING,
        message="  report failed  ",
        field_name="  report  ",
    )

    assert error.message == "report failed"
    assert error.field_name == "report"

    with pytest.raises(ValueError, match="message cannot be blank"):
        OfflineResearchScenarioError(
            stage=OfflineResearchScenarioStage.REPORTING,
            message="   ",
        )


def test_result_validates_embedded_types_and_success_property() -> None:
    success_result = OfflineResearchScenarioService().execute(make_request())

    assert success_result.successful is True
    assert OfflineResearchScenarioResult(scenario_id="b7-incomplete").successful is False

    with pytest.raises(
        ValueError,
        match="ingestion_result must be an OfflineDatasetIngestionResult",
    ):
        OfflineResearchScenarioResult(
            scenario_id="b7-invalid-ingestion",
            ingestion_result=object(),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="errors must contain only OfflineResearchScenarioError"):
        OfflineResearchScenarioResult(
            scenario_id="b7-invalid-errors",
            errors=(object(),),  # type: ignore[arg-type]
        )
