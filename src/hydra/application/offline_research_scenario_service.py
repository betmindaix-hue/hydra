from __future__ import annotations

from typing import Protocol

from hydra.application.backtesting_dto import BacktestRequest, BacktestRunSummary
from hydra.application.backtesting_service import OfflineBacktestingService
from hydra.application.market_data_ingestion_dto import (
    OfflineDatasetIngestionRequest,
    OfflineDatasetIngestionResult,
)
from hydra.application.market_data_ingestion_service import OfflineMarketDataIngestionService
from hydra.application.offline_research_scenario_dto import (
    OfflineResearchScenarioError,
    OfflineResearchScenarioRequest,
    OfflineResearchScenarioResult,
    OfflineResearchScenarioStage,
)
from hydra.application.research_reporting_dto import (
    ResearchReportGenerationResult,
    ResearchReportRequest,
)
from hydra.application.research_reporting_service import OfflineResearchReportingService
from hydra.application.strategy_research_dto import StrategyResearchRequest
from hydra.application.strategy_research_service import OfflineStrategyResearchService


class OfflineDatasetIngestionServicePort(Protocol):
    def execute(self, request: OfflineDatasetIngestionRequest) -> OfflineDatasetIngestionResult:
        """Execute offline dataset ingestion."""


class OfflineBacktestingServicePort(Protocol):
    def execute(self, request: BacktestRequest) -> BacktestRunSummary:
        """Execute offline backtesting."""


class OfflineResearchReportingServicePort(Protocol):
    def generate(self, request: ResearchReportRequest) -> ResearchReportGenerationResult:
        """Generate an offline research report."""


class OfflineResearchScenarioService:
    def __init__(
        self,
        *,
        ingestion_service: OfflineDatasetIngestionServicePort | None = None,
        backtesting_service: OfflineBacktestingServicePort | None = None,
        reporting_service: OfflineResearchReportingServicePort | None = None,
    ) -> None:
        self._ingestion_service = ingestion_service or OfflineMarketDataIngestionService()
        self._backtesting_service = backtesting_service or OfflineBacktestingService()
        self._reporting_service = reporting_service or OfflineResearchReportingService()

    def execute(self, request: object) -> OfflineResearchScenarioResult:
        if not isinstance(request, OfflineResearchScenarioRequest):
            return OfflineResearchScenarioResult(
                scenario_id="invalid-request",
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.INGESTION,
                        message="OfflineResearchScenarioRequest is required.",
                        field_name="request",
                    ),
                ),
            )

        ingestion_result = self._ingestion_service.execute(
            OfflineDatasetIngestionRequest(
                dataset_name=request.dataset_name,
                records=request.records,
            )
        )
        if not ingestion_result.series:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.INGESTION,
                        message=self._compose_zero_series_message(ingestion_result),
                        field_name="series",
                    ),
                ),
            )
        if len(ingestion_result.series) > 1:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.INGESTION,
                        message=(
                            "Offline dataset ingestion must produce exactly one "
                            f"MarketDataSeries, but returned {len(ingestion_result.series)}."
                        ),
                        field_name="series",
                    ),
                ),
            )
        if not ingestion_result.is_successful:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.INGESTION,
                        message=self._summarize_errors(
                            ingestion_result.errors,
                            fallback_message=(
                                "Offline dataset ingestion failed before scenario handoff."
                            ),
                        ),
                        field_name=self._resolve_field_name(
                            ingestion_result.errors,
                            default_field_name="records",
                        ),
                    ),
                ),
            )

        strategy_service = OfflineStrategyResearchService(request.strategy_provider)
        strategy_result = strategy_service.execute(
            StrategyResearchRequest(
                research_id=request.research_id,
                market_data_series=ingestion_result.series[0],
                start_timestamp=request.start_timestamp,
                end_timestamp=request.end_timestamp,
            )
        )
        if not strategy_result.successful:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                strategy_research_result=strategy_result,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.STRATEGY_RESEARCH,
                        message=self._summarize_errors(
                            strategy_result.errors,
                            fallback_message="Offline strategy research failed.",
                        ),
                        field_name=self._resolve_field_name(
                            strategy_result.errors,
                            default_field_name="strategy_research_result",
                        ),
                    ),
                ),
            )

        try:
            backtest_request = strategy_result.to_backtest_request(
                backtest_id=request.backtest_id,
                initial_cash=request.initial_cash,
            )
        except ValueError as exc:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                strategy_research_result=strategy_result,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.STRATEGY_RESEARCH,
                        message=str(exc),
                        field_name="strategy_research_result",
                    ),
                ),
            )

        backtest_summary = self._backtesting_service.execute(backtest_request)
        if not backtest_summary.successful:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                strategy_research_result=strategy_result,
                backtest_summary=backtest_summary,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.BACKTESTING,
                        message=self._summarize_errors(
                            backtest_summary.errors,
                            fallback_message="Offline backtesting failed.",
                        ),
                        field_name=self._resolve_field_name(
                            backtest_summary.errors,
                            default_field_name="backtest_summary",
                        ),
                    ),
                ),
            )

        if backtest_summary.result is None:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                strategy_research_result=strategy_result,
                backtest_summary=backtest_summary,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.BACKTESTING,
                        message="Offline backtesting did not return a BacktestResult.",
                        field_name="backtest_summary",
                    ),
                ),
            )

        try:
            report_request = ResearchReportRequest(
                report_id=request.report_id,
                backtest_result=backtest_summary.result,
                strategy_research_result=strategy_result,
                title=request.title,
                notes=request.notes,
            )
        except ValueError as exc:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                strategy_research_result=strategy_result,
                backtest_summary=backtest_summary,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.REPORTING,
                        message=str(exc),
                        field_name="report_request",
                    ),
                ),
            )

        report_generation_result = self._reporting_service.generate(report_request)
        if not report_generation_result.successful:
            return OfflineResearchScenarioResult(
                scenario_id=request.scenario_id,
                ingestion_result=ingestion_result,
                strategy_research_result=strategy_result,
                backtest_summary=backtest_summary,
                report_generation_result=report_generation_result,
                errors=(
                    OfflineResearchScenarioError(
                        stage=OfflineResearchScenarioStage.REPORTING,
                        message=self._summarize_errors(
                            report_generation_result.errors,
                            fallback_message="Offline report generation failed.",
                        ),
                        field_name=self._resolve_field_name(
                            report_generation_result.errors,
                            default_field_name="report_generation_result",
                        ),
                    ),
                ),
            )

        return OfflineResearchScenarioResult(
            scenario_id=request.scenario_id,
            ingestion_result=ingestion_result,
            strategy_research_result=strategy_result,
            backtest_summary=backtest_summary,
            report_generation_result=report_generation_result,
        )

    def _compose_zero_series_message(self, ingestion_result: object) -> str:
        error_summary = self._summarize_errors(
            getattr(ingestion_result, "errors", ()),
            fallback_message="Offline dataset ingestion did not produce a MarketDataSeries.",
        )
        if error_summary == "Offline dataset ingestion did not produce a MarketDataSeries.":
            return error_summary
        return "Offline dataset ingestion did not produce a MarketDataSeries. " + error_summary

    def _resolve_field_name(
        self,
        errors: tuple[object, ...],
        *,
        default_field_name: str,
    ) -> str:
        for error in errors:
            field_name = getattr(error, "field_name", None)
            if isinstance(field_name, str) and field_name.strip():
                return field_name.strip()
        return default_field_name

    def _summarize_errors(
        self,
        errors: tuple[object, ...],
        *,
        fallback_message: str,
    ) -> str:
        messages: list[str] = []
        for error in errors:
            message = getattr(error, "message", None)
            if not isinstance(message, str):
                continue

            normalized = message.strip()
            if normalized and normalized not in messages:
                messages.append(normalized)

        if messages:
            return "; ".join(messages)
        return fallback_message
