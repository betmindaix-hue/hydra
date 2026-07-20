from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from hydra.application.offline_research_scenario_dto import OfflineResearchScenarioResult
from hydra.domain.backtesting import BacktestResult
from hydra.domain.market_data import Market, Symbol, Timeframe
from hydra.domain.research_reporting import ResearchReport


def _normalize_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string.")
    return value.strip()


def _normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")

    normalized = value.strip()
    return normalized or None


def _normalize_notes(notes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(notes, str):
        raise ValueError("ResearchRunRecord notes must be an iterable of strings.")

    normalized_notes: list[str] = []
    for note in notes:
        if not isinstance(note, str):
            raise ValueError("ResearchRunRecord notes must contain only strings.")

        normalized = note.strip()
        if normalized:
            normalized_notes.append(normalized)

    return tuple(normalized_notes)


def _normalize_optional_symbol(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    return Symbol(value).value


def _normalize_optional_market(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    del field_name
    return Market(value).value


def _normalize_optional_timeframe(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string when provided.")
    return Timeframe(value.strip()).value


def _normalize_optional_scenario_id(value: str | None, *, field_name: str) -> str | None:
    return _normalize_optional_text(value, field_name=field_name)


def _require_bool(value: bool, *, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a bool.")


def _require_count(value: int, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")


def _require_optional_float(value: float | None, *, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number when provided.")
    return float(value)


def _require_optional_int(value: int | None, *, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer when provided.")
    return value


def _resolve_backtest_result(
    scenario_result: OfflineResearchScenarioResult,
) -> BacktestResult | None:
    backtest_summary = scenario_result.backtest_summary
    if backtest_summary is None:
        return None
    return backtest_summary.result


def _resolve_report(
    scenario_result: OfflineResearchScenarioResult,
) -> ResearchReport | None:
    report_generation_result = scenario_result.report_generation_result
    if report_generation_result is None:
        return None
    return report_generation_result.report


class ResearchRunStatus(StrEnum):
    SUCCESSFUL = "successful"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ResearchRunRecord:
    scenario_id: str
    status: ResearchRunStatus
    scenario_result: OfflineResearchScenarioResult
    title: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ResearchRunStatus):
            raise ValueError("ResearchRunRecord status must be a ResearchRunStatus.")
        if not isinstance(self.scenario_result, OfflineResearchScenarioResult):
            raise ValueError(
                "ResearchRunRecord scenario_result must be an OfflineResearchScenarioResult."
            )

        normalized_scenario_id = _normalize_identifier(
            self.scenario_id,
            field_name="ResearchRunRecord scenario_id",
        )
        if normalized_scenario_id != self.scenario_result.scenario_id:
            raise ValueError(
                "ResearchRunRecord scenario_id must match OfflineResearchScenarioResult "
                "scenario_id."
            )

        expected_status = (
            ResearchRunStatus.SUCCESSFUL
            if self.scenario_result.successful
            else ResearchRunStatus.FAILED
        )
        if self.status is not expected_status:
            raise ValueError(
                "ResearchRunRecord status must match OfflineResearchScenarioResult success "
                "state."
            )

        object.__setattr__(self, "scenario_id", normalized_scenario_id)
        object.__setattr__(
            self,
            "title",
            _normalize_optional_text(
                self.title,
                field_name="ResearchRunRecord title",
            ),
        )
        object.__setattr__(self, "notes", _normalize_notes(self.notes))

    @property
    def successful(self) -> bool:
        return self.status is ResearchRunStatus.SUCCESSFUL

    @property
    def has_report(self) -> bool:
        return _resolve_report(self.scenario_result) is not None

    @property
    def has_backtest(self) -> bool:
        return _resolve_backtest_result(self.scenario_result) is not None

    @property
    def symbol(self) -> str | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.symbol.value

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None:
            return backtest_result.symbol.value
        return None

    @property
    def market(self) -> str | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.market.value

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None:
            return backtest_result.market.value
        return None

    @property
    def timeframe(self) -> str | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.timeframe.value

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None:
            return backtest_result.timeframe.value
        return None

    @property
    def total_return(self) -> float | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.metrics.total_return

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None and backtest_result.metrics is not None:
            return backtest_result.metrics.total_return
        return None

    @property
    def max_drawdown(self) -> float | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.risk.max_drawdown

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None and backtest_result.metrics is not None:
            return backtest_result.metrics.max_drawdown
        return None

    @property
    def trade_count(self) -> int | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.metrics.trade_count

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None and backtest_result.metrics is not None:
            return backtest_result.metrics.trade_count
        return None

    @property
    def signal_count(self) -> int | None:
        report = _resolve_report(self.scenario_result)
        if report is not None:
            return report.metrics.signal_count

        backtest_result = _resolve_backtest_result(self.scenario_result)
        if backtest_result is not None:
            return backtest_result.signal_count
        return None


@dataclass(frozen=True, slots=True)
class ResearchRunCatalogError:
    message: str
    field_name: str | None = None
    scenario_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("ResearchRunCatalogError message cannot be blank.")

        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(
            self,
            "field_name",
            _normalize_optional_text(
                self.field_name,
                field_name="ResearchRunCatalogError field_name",
            ),
        )
        object.__setattr__(
            self,
            "scenario_id",
            _normalize_optional_scenario_id(
                self.scenario_id,
                field_name="ResearchRunCatalogError scenario_id",
            ),
        )


@dataclass(frozen=True, slots=True)
class ResearchRunCatalogAddResult:
    record: ResearchRunRecord | None = None
    errors: tuple[ResearchRunCatalogError, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.record is not None and not isinstance(self.record, ResearchRunRecord):
            raise ValueError("ResearchRunCatalogAddResult record must be a ResearchRunRecord.")

        normalized_errors = tuple(self.errors)
        for error in normalized_errors:
            if not isinstance(error, ResearchRunCatalogError):
                raise ValueError(
                    "ResearchRunCatalogAddResult errors must contain only "
                    "ResearchRunCatalogError values."
                )

        if self.record is not None and normalized_errors:
            raise ValueError("ResearchRunCatalogAddResult cannot contain both a record and errors.")

        object.__setattr__(self, "errors", normalized_errors)

    @property
    def successful(self) -> bool:
        return self.record is not None and not self.errors


@dataclass(frozen=True, slots=True)
class ResearchRunCatalogQuery:
    status: ResearchRunStatus | None = None
    symbol: str | None = None
    market: str | None = None
    timeframe: str | None = None
    require_report: bool = False
    require_backtest: bool = False

    def __post_init__(self) -> None:
        if self.status is not None and not isinstance(self.status, ResearchRunStatus):
            raise ValueError("ResearchRunCatalogQuery status must be a ResearchRunStatus.")

        _require_bool(self.require_report, field_name="ResearchRunCatalogQuery require_report")
        _require_bool(
            self.require_backtest,
            field_name="ResearchRunCatalogQuery require_backtest",
        )

        object.__setattr__(
            self,
            "symbol",
            _normalize_optional_symbol(
                self.symbol,
                field_name="ResearchRunCatalogQuery symbol",
            ),
        )
        object.__setattr__(
            self,
            "market",
            _normalize_optional_market(
                self.market,
                field_name="ResearchRunCatalogQuery market",
            ),
        )
        object.__setattr__(
            self,
            "timeframe",
            _normalize_optional_timeframe(
                self.timeframe,
                field_name="ResearchRunCatalogQuery timeframe",
            ),
        )


@dataclass(frozen=True, slots=True)
class ResearchRunComparisonSummary:
    run_count: int
    successful_run_count: int
    failed_run_count: int
    best_total_return_scenario_id: str | None = None
    best_total_return: float | None = None
    lowest_max_drawdown_scenario_id: str | None = None
    lowest_max_drawdown: float | None = None
    highest_trade_count_scenario_id: str | None = None
    highest_trade_count: int | None = None

    def __post_init__(self) -> None:
        _require_count(self.run_count, field_name="ResearchRunComparisonSummary run_count")
        _require_count(
            self.successful_run_count,
            field_name="ResearchRunComparisonSummary successful_run_count",
        )
        _require_count(
            self.failed_run_count,
            field_name="ResearchRunComparisonSummary failed_run_count",
        )

        if self.successful_run_count + self.failed_run_count != self.run_count:
            raise ValueError(
                "ResearchRunComparisonSummary successful_run_count and "
                "failed_run_count must add up to run_count."
            )

        best_total_return_scenario_id = _normalize_optional_scenario_id(
            self.best_total_return_scenario_id,
            field_name="ResearchRunComparisonSummary best_total_return_scenario_id",
        )
        best_total_return = _require_optional_float(
            self.best_total_return,
            field_name="ResearchRunComparisonSummary best_total_return",
        )
        lowest_max_drawdown_scenario_id = _normalize_optional_scenario_id(
            self.lowest_max_drawdown_scenario_id,
            field_name="ResearchRunComparisonSummary lowest_max_drawdown_scenario_id",
        )
        lowest_max_drawdown = _require_optional_float(
            self.lowest_max_drawdown,
            field_name="ResearchRunComparisonSummary lowest_max_drawdown",
        )
        highest_trade_count_scenario_id = _normalize_optional_scenario_id(
            self.highest_trade_count_scenario_id,
            field_name="ResearchRunComparisonSummary highest_trade_count_scenario_id",
        )
        highest_trade_count = _require_optional_int(
            self.highest_trade_count,
            field_name="ResearchRunComparisonSummary highest_trade_count",
        )

        self._validate_pair(
            best_total_return_scenario_id,
            best_total_return,
            pair_name="best_total_return",
        )
        self._validate_pair(
            lowest_max_drawdown_scenario_id,
            lowest_max_drawdown,
            pair_name="lowest_max_drawdown",
        )
        self._validate_pair(
            highest_trade_count_scenario_id,
            highest_trade_count,
            pair_name="highest_trade_count",
        )

        object.__setattr__(
            self,
            "best_total_return_scenario_id",
            best_total_return_scenario_id,
        )
        object.__setattr__(self, "best_total_return", best_total_return)
        object.__setattr__(
            self,
            "lowest_max_drawdown_scenario_id",
            lowest_max_drawdown_scenario_id,
        )
        object.__setattr__(self, "lowest_max_drawdown", lowest_max_drawdown)
        object.__setattr__(
            self,
            "highest_trade_count_scenario_id",
            highest_trade_count_scenario_id,
        )
        object.__setattr__(self, "highest_trade_count", highest_trade_count)

    def _validate_pair(
        self,
        scenario_id: str | None,
        metric: float | int | None,
        *,
        pair_name: str,
    ) -> None:
        if scenario_id is None and metric is None:
            return
        if scenario_id is None or metric is None:
            raise ValueError(
                "ResearchRunComparisonSummary "
                f"{pair_name} scenario_id and metric must both be provided together."
            )
