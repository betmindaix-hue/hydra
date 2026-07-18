from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from hydra.application.strategy_research_dto import StrategyResearchResult
from hydra.domain.backtesting import BacktestResult
from hydra.domain.research_reporting import ResearchReport, ResearchReportId


def _normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")

    normalized = value.strip()
    return normalized or None


def _normalize_notes(notes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(notes, str):
        raise ValueError("ResearchReportRequest notes must be an iterable of strings.")

    normalized_notes: list[str] = []
    for note in notes:
        if not isinstance(note, str):
            raise ValueError("ResearchReportRequest notes must contain only strings.")

        normalized = note.strip()
        if normalized:
            normalized_notes.append(normalized)

    return tuple(normalized_notes)


@dataclass(frozen=True, slots=True)
class ResearchReportRequest:
    report_id: str
    backtest_result: BacktestResult
    strategy_research_result: StrategyResearchResult | None = None
    title: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        normalized_report_id = ResearchReportId(self.report_id)
        if not isinstance(self.backtest_result, BacktestResult):
            raise ValueError("ResearchReportRequest backtest_result must be a BacktestResult.")
        if self.strategy_research_result is not None and not isinstance(
            self.strategy_research_result,
            StrategyResearchResult,
        ):
            raise ValueError(
                "ResearchReportRequest strategy_research_result must be a "
                "StrategyResearchResult when provided."
            )

        object.__setattr__(self, "report_id", normalized_report_id.value)
        object.__setattr__(
            self,
            "title",
            _normalize_optional_text(
                self.title,
                field_name="ResearchReportRequest title",
            ),
        )
        object.__setattr__(self, "notes", _normalize_notes(self.notes))


@dataclass(frozen=True, slots=True)
class ResearchReportGenerationError:
    message: str
    field_name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("ResearchReportGenerationError message cannot be blank.")

        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(
            self,
            "field_name",
            _normalize_optional_text(
                self.field_name,
                field_name="ResearchReportGenerationError field_name",
            ),
        )


@dataclass(frozen=True, slots=True)
class ResearchReportGenerationResult:
    report: ResearchReport | None = None
    errors: tuple[ResearchReportGenerationError, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        normalized_errors = tuple(self.errors)
        for error in normalized_errors:
            if not isinstance(error, ResearchReportGenerationError):
                raise ValueError(
                    "ResearchReportGenerationResult errors must contain only "
                    "ResearchReportGenerationError values."
                )

        if self.report is not None and not isinstance(self.report, ResearchReport):
            raise ValueError("ResearchReportGenerationResult report must be a ResearchReport.")
        if normalized_errors and self.report is not None:
            raise ValueError(
                "ResearchReportGenerationResult cannot contain both a report and errors."
            )

        object.__setattr__(self, "errors", normalized_errors)

    @property
    def successful(self) -> bool:
        return self.report is not None and not self.errors
