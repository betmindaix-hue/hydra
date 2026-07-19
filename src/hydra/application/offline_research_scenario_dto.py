from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import cast

from hydra.application.backtesting_dto import BacktestRunSummary
from hydra.application.market_data_ingestion_dto import (
    OfflineDatasetIngestionResult,
    OfflineMarketDataRecord,
)
from hydra.application.research_reporting_dto import ResearchReportGenerationResult
from hydra.application.strategy_research_dto import StrategyResearchResult
from hydra.ports.strategy_research import StrategyResearchProviderPort


def _normalize_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string.")
    return value.strip()


def _normalize_optional_timestamp(
    value: datetime | None,
    *,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime when provided.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
    return value


def _normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")

    normalized = value.strip()
    return normalized or None


def _normalize_records(
    records: Iterable[OfflineMarketDataRecord],
) -> tuple[OfflineMarketDataRecord, ...]:
    if isinstance(records, str):
        raise ValueError("OfflineResearchScenarioRequest records must be an iterable.")

    try:
        normalized_records = tuple(records)
    except TypeError as exc:
        raise ValueError("OfflineResearchScenarioRequest records must be an iterable.") from exc

    if not normalized_records:
        raise ValueError("OfflineResearchScenarioRequest records must not be empty.")

    for record in normalized_records:
        if not isinstance(record, OfflineMarketDataRecord):
            raise ValueError(
                "OfflineResearchScenarioRequest records must contain only "
                "OfflineMarketDataRecord values."
            )

    return normalized_records


def _normalize_notes(notes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(notes, str):
        raise ValueError("OfflineResearchScenarioRequest notes must be an iterable of strings.")

    normalized_notes: list[str] = []
    for note in notes:
        if not isinstance(note, str):
            raise ValueError("OfflineResearchScenarioRequest notes must contain only strings.")

        normalized = note.strip()
        if normalized:
            normalized_notes.append(normalized)

    return tuple(normalized_notes)


def _normalize_strategy_provider(provider: object) -> StrategyResearchProviderPort:
    if isinstance(provider, StrategyResearchProviderPort):
        return provider

    generate_signals = getattr(provider, "generate_signals", None)
    if callable(generate_signals):
        return cast(StrategyResearchProviderPort, provider)

    raise ValueError(
        "OfflineResearchScenarioRequest strategy_provider must implement "
        "StrategyResearchProviderPort or expose callable generate_signals."
    )


class OfflineResearchScenarioStage(StrEnum):
    INGESTION = "ingestion"
    STRATEGY_RESEARCH = "strategy_research"
    BACKTESTING = "backtesting"
    REPORTING = "reporting"


@dataclass(frozen=True, slots=True)
class OfflineResearchScenarioRequest:
    scenario_id: str
    dataset_name: str
    records: tuple[OfflineMarketDataRecord, ...]
    strategy_provider: StrategyResearchProviderPort
    research_id: str
    backtest_id: str
    report_id: str
    initial_cash: float
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    title: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        normalized_start = _normalize_optional_timestamp(
            self.start_timestamp,
            field_name="OfflineResearchScenarioRequest start_timestamp",
        )
        normalized_end = _normalize_optional_timestamp(
            self.end_timestamp,
            field_name="OfflineResearchScenarioRequest end_timestamp",
        )
        if (
            normalized_start is not None
            and normalized_end is not None
            and normalized_start >= normalized_end
        ):
            raise ValueError(
                "OfflineResearchScenarioRequest start_timestamp must be before end_timestamp."
            )
        if isinstance(self.initial_cash, bool) or not isinstance(self.initial_cash, (int, float)):
            raise ValueError("OfflineResearchScenarioRequest initial_cash must be numeric.")
        if self.initial_cash <= 0:
            raise ValueError("OfflineResearchScenarioRequest initial_cash must be positive.")

        object.__setattr__(
            self,
            "scenario_id",
            _normalize_identifier(
                self.scenario_id,
                field_name="OfflineResearchScenarioRequest scenario_id",
            ),
        )
        object.__setattr__(
            self,
            "dataset_name",
            _normalize_identifier(
                self.dataset_name,
                field_name="OfflineResearchScenarioRequest dataset_name",
            ),
        )
        object.__setattr__(self, "records", _normalize_records(self.records))
        object.__setattr__(
            self,
            "strategy_provider",
            _normalize_strategy_provider(self.strategy_provider),
        )
        object.__setattr__(
            self,
            "research_id",
            _normalize_identifier(
                self.research_id,
                field_name="OfflineResearchScenarioRequest research_id",
            ),
        )
        object.__setattr__(
            self,
            "backtest_id",
            _normalize_identifier(
                self.backtest_id,
                field_name="OfflineResearchScenarioRequest backtest_id",
            ),
        )
        object.__setattr__(
            self,
            "report_id",
            _normalize_identifier(
                self.report_id,
                field_name="OfflineResearchScenarioRequest report_id",
            ),
        )
        object.__setattr__(self, "initial_cash", float(self.initial_cash))
        object.__setattr__(self, "start_timestamp", normalized_start)
        object.__setattr__(self, "end_timestamp", normalized_end)
        object.__setattr__(
            self,
            "title",
            _normalize_optional_text(
                self.title,
                field_name="OfflineResearchScenarioRequest title",
            ),
        )
        object.__setattr__(self, "notes", _normalize_notes(self.notes))


@dataclass(frozen=True, slots=True)
class OfflineResearchScenarioError:
    stage: OfflineResearchScenarioStage
    message: str
    field_name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage, OfflineResearchScenarioStage):
            raise ValueError(
                "OfflineResearchScenarioError stage must be an OfflineResearchScenarioStage."
            )
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("OfflineResearchScenarioError message cannot be blank.")

        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(
            self,
            "field_name",
            _normalize_optional_text(
                self.field_name,
                field_name="OfflineResearchScenarioError field_name",
            ),
        )


@dataclass(frozen=True, slots=True)
class OfflineResearchScenarioResult:
    scenario_id: str
    ingestion_result: OfflineDatasetIngestionResult | None = None
    strategy_research_result: StrategyResearchResult | None = None
    backtest_summary: BacktestRunSummary | None = None
    report_generation_result: ResearchReportGenerationResult | None = None
    errors: tuple[OfflineResearchScenarioError, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scenario_id",
            _normalize_identifier(
                self.scenario_id,
                field_name="OfflineResearchScenarioResult scenario_id",
            ),
        )

        if self.ingestion_result is not None and not isinstance(
            self.ingestion_result,
            OfflineDatasetIngestionResult,
        ):
            raise ValueError(
                "OfflineResearchScenarioResult ingestion_result must be an "
                "OfflineDatasetIngestionResult."
            )
        if self.strategy_research_result is not None and not isinstance(
            self.strategy_research_result,
            StrategyResearchResult,
        ):
            raise ValueError(
                "OfflineResearchScenarioResult strategy_research_result must be a "
                "StrategyResearchResult."
            )
        if self.backtest_summary is not None and not isinstance(
            self.backtest_summary,
            BacktestRunSummary,
        ):
            raise ValueError(
                "OfflineResearchScenarioResult backtest_summary must be a BacktestRunSummary."
            )
        if self.report_generation_result is not None and not isinstance(
            self.report_generation_result,
            ResearchReportGenerationResult,
        ):
            raise ValueError(
                "OfflineResearchScenarioResult report_generation_result must be a "
                "ResearchReportGenerationResult."
            )

        normalized_errors = tuple(self.errors)
        for error in normalized_errors:
            if not isinstance(error, OfflineResearchScenarioError):
                raise ValueError(
                    "OfflineResearchScenarioResult errors must contain only "
                    "OfflineResearchScenarioError values."
                )

        object.__setattr__(self, "errors", normalized_errors)

    @property
    def successful(self) -> bool:
        return (
            not self.errors
            and self.ingestion_result is not None
            and self.ingestion_result.is_successful
            and self.strategy_research_result is not None
            and self.strategy_research_result.successful
            and self.backtest_summary is not None
            and self.backtest_summary.successful
            and self.report_generation_result is not None
            and self.report_generation_result.successful
        )
