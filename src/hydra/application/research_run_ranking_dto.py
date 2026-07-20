from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from hydra.application.research_run_catalog_dto import ResearchRunRecord, ResearchRunStatus
from hydra.domain.market_data import Market, Symbol, Timeframe


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


def _normalize_optional_symbol(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    del field_name
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


def _require_bool(value: bool, *, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a bool.")


def _require_non_negative_int(value: int, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
    return value


def _require_positive_int(value: int, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return value


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


def _validate_min_max_pair(
    minimum: float | int | None,
    maximum: float | int | None,
    *,
    field_name: str,
) -> None:
    if minimum is None or maximum is None:
        return
    if minimum > maximum:
        raise ValueError(f"{field_name} minimum cannot exceed maximum.")


class ResearchRunRankingMetric(StrEnum):
    TOTAL_RETURN = "total_return"
    MAX_DRAWDOWN = "max_drawdown"
    TRADE_COUNT = "trade_count"
    SIGNAL_COUNT = "signal_count"


class ResearchRunRankingDirection(StrEnum):
    HIGHER_FIRST = "higher_first"
    LOWER_FIRST = "lower_first"


def _default_direction_for_metric(
    metric: ResearchRunRankingMetric,
) -> ResearchRunRankingDirection:
    if metric is ResearchRunRankingMetric.MAX_DRAWDOWN:
        return ResearchRunRankingDirection.LOWER_FIRST
    return ResearchRunRankingDirection.HIGHER_FIRST


@dataclass(frozen=True, slots=True)
class ResearchRunEligibilityCriteria:
    status: ResearchRunStatus | None = ResearchRunStatus.SUCCESSFUL
    symbol: str | None = None
    market: str | None = None
    timeframe: str | None = None
    require_report: bool = False
    require_backtest: bool = False
    min_total_return: float | None = None
    max_total_return: float | None = None
    min_max_drawdown: float | None = None
    max_max_drawdown: float | None = None
    min_trade_count: int | None = None
    max_trade_count: int | None = None
    min_signal_count: int | None = None
    max_signal_count: int | None = None

    def __post_init__(self) -> None:
        if self.status is not None and not isinstance(self.status, ResearchRunStatus):
            raise ValueError("ResearchRunEligibilityCriteria status must be a ResearchRunStatus.")

        _require_bool(
            self.require_report,
            field_name="ResearchRunEligibilityCriteria require_report",
        )
        _require_bool(
            self.require_backtest,
            field_name="ResearchRunEligibilityCriteria require_backtest",
        )

        min_total_return = _require_optional_float(
            self.min_total_return,
            field_name="ResearchRunEligibilityCriteria min_total_return",
        )
        max_total_return = _require_optional_float(
            self.max_total_return,
            field_name="ResearchRunEligibilityCriteria max_total_return",
        )
        min_max_drawdown = _require_optional_float(
            self.min_max_drawdown,
            field_name="ResearchRunEligibilityCriteria min_max_drawdown",
        )
        max_max_drawdown = _require_optional_float(
            self.max_max_drawdown,
            field_name="ResearchRunEligibilityCriteria max_max_drawdown",
        )
        min_trade_count = _require_optional_int(
            self.min_trade_count,
            field_name="ResearchRunEligibilityCriteria min_trade_count",
        )
        max_trade_count = _require_optional_int(
            self.max_trade_count,
            field_name="ResearchRunEligibilityCriteria max_trade_count",
        )
        min_signal_count = _require_optional_int(
            self.min_signal_count,
            field_name="ResearchRunEligibilityCriteria min_signal_count",
        )
        max_signal_count = _require_optional_int(
            self.max_signal_count,
            field_name="ResearchRunEligibilityCriteria max_signal_count",
        )

        _validate_min_max_pair(
            min_total_return,
            max_total_return,
            field_name="ResearchRunEligibilityCriteria total_return",
        )
        _validate_min_max_pair(
            min_max_drawdown,
            max_max_drawdown,
            field_name="ResearchRunEligibilityCriteria max_drawdown",
        )
        _validate_min_max_pair(
            min_trade_count,
            max_trade_count,
            field_name="ResearchRunEligibilityCriteria trade_count",
        )
        _validate_min_max_pair(
            min_signal_count,
            max_signal_count,
            field_name="ResearchRunEligibilityCriteria signal_count",
        )

        object.__setattr__(
            self,
            "symbol",
            _normalize_optional_symbol(
                self.symbol,
                field_name="ResearchRunEligibilityCriteria symbol",
            ),
        )
        object.__setattr__(
            self,
            "market",
            _normalize_optional_market(
                self.market,
                field_name="ResearchRunEligibilityCriteria market",
            ),
        )
        object.__setattr__(
            self,
            "timeframe",
            _normalize_optional_timeframe(
                self.timeframe,
                field_name="ResearchRunEligibilityCriteria timeframe",
            ),
        )
        object.__setattr__(self, "min_total_return", min_total_return)
        object.__setattr__(self, "max_total_return", max_total_return)
        object.__setattr__(self, "min_max_drawdown", min_max_drawdown)
        object.__setattr__(self, "max_max_drawdown", max_max_drawdown)
        object.__setattr__(self, "min_trade_count", min_trade_count)
        object.__setattr__(self, "max_trade_count", max_trade_count)
        object.__setattr__(self, "min_signal_count", min_signal_count)
        object.__setattr__(self, "max_signal_count", max_signal_count)


@dataclass(frozen=True, slots=True)
class ResearchRunRankingSpec:
    metric: ResearchRunRankingMetric
    direction: ResearchRunRankingDirection | None = None
    eligibility: ResearchRunEligibilityCriteria = field(
        default_factory=ResearchRunEligibilityCriteria
    )
    require_metric: bool = True
    limit: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.metric, ResearchRunRankingMetric):
            raise ValueError("ResearchRunRankingSpec metric must be a ResearchRunRankingMetric.")
        if self.direction is not None and not isinstance(
            self.direction,
            ResearchRunRankingDirection,
        ):
            raise ValueError(
                "ResearchRunRankingSpec direction must be a ResearchRunRankingDirection."
            )
        if not isinstance(self.eligibility, ResearchRunEligibilityCriteria):
            raise ValueError(
                "ResearchRunRankingSpec eligibility must be a ResearchRunEligibilityCriteria."
            )

        _require_bool(
            self.require_metric,
            field_name="ResearchRunRankingSpec require_metric",
        )

        normalized_limit = self.limit
        if normalized_limit is not None:
            normalized_limit = _require_positive_int(
                normalized_limit,
                field_name="ResearchRunRankingSpec limit",
            )

        object.__setattr__(self, "limit", normalized_limit)

    @property
    def resolved_direction(self) -> ResearchRunRankingDirection:
        if self.direction is not None:
            return self.direction
        return _default_direction_for_metric(self.metric)


@dataclass(frozen=True, slots=True)
class ResearchRunRankingEntry:
    rank: int
    scenario_id: str
    record: ResearchRunRecord
    metric: ResearchRunRankingMetric
    metric_value: float | int
    insertion_index: int

    def __post_init__(self) -> None:
        normalized_rank = _require_positive_int(
            self.rank,
            field_name="ResearchRunRankingEntry rank",
        )
        normalized_scenario_id = _normalize_identifier(
            self.scenario_id,
            field_name="ResearchRunRankingEntry scenario_id",
        )
        if not isinstance(self.record, ResearchRunRecord):
            raise ValueError("ResearchRunRankingEntry record must be a ResearchRunRecord.")
        if normalized_scenario_id != self.record.scenario_id:
            raise ValueError(
                "ResearchRunRankingEntry scenario_id must match ResearchRunRecord scenario_id."
            )
        if not isinstance(self.metric, ResearchRunRankingMetric):
            raise ValueError("ResearchRunRankingEntry metric must be a ResearchRunRankingMetric.")
        if isinstance(self.metric_value, bool) or not isinstance(self.metric_value, (int, float)):
            raise ValueError("ResearchRunRankingEntry metric_value must be numeric.")

        normalized_insertion_index = _require_non_negative_int(
            self.insertion_index,
            field_name="ResearchRunRankingEntry insertion_index",
        )

        object.__setattr__(self, "rank", normalized_rank)
        object.__setattr__(self, "scenario_id", normalized_scenario_id)
        object.__setattr__(self, "insertion_index", normalized_insertion_index)


@dataclass(frozen=True, slots=True)
class ResearchRunExclusionReason:
    scenario_id: str
    reason: str
    field_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scenario_id",
            _normalize_identifier(
                self.scenario_id,
                field_name="ResearchRunExclusionReason scenario_id",
            ),
        )
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("ResearchRunExclusionReason reason cannot be blank.")

        object.__setattr__(self, "reason", self.reason.strip())
        object.__setattr__(
            self,
            "field_name",
            _normalize_optional_text(
                self.field_name,
                field_name="ResearchRunExclusionReason field_name",
            ),
        )


@dataclass(frozen=True, slots=True)
class ResearchRunRankingResult:
    entries: tuple[ResearchRunRankingEntry, ...] = field(default_factory=tuple)
    excluded: tuple[ResearchRunExclusionReason, ...] = field(default_factory=tuple)
    considered_count: int = 0

    def __post_init__(self) -> None:
        normalized_entries = tuple(self.entries)
        normalized_excluded = tuple(self.excluded)

        for entry in normalized_entries:
            if not isinstance(entry, ResearchRunRankingEntry):
                raise ValueError(
                    "ResearchRunRankingResult entries must contain only "
                    "ResearchRunRankingEntry values."
                )

        for reason in normalized_excluded:
            if not isinstance(reason, ResearchRunExclusionReason):
                raise ValueError(
                    "ResearchRunRankingResult excluded must contain only "
                    "ResearchRunExclusionReason values."
                )

        normalized_considered_count = _require_non_negative_int(
            self.considered_count,
            field_name="ResearchRunRankingResult considered_count",
        )
        minimum_considered_count = len(normalized_entries) + len(normalized_excluded)
        if normalized_considered_count < minimum_considered_count:
            raise ValueError(
                "ResearchRunRankingResult considered_count cannot be less than the number "
                "of returned entries and exclusions."
            )

        entry_scenario_ids: set[str] = set()
        for expected_rank, entry in enumerate(normalized_entries, start=1):
            if entry.rank != expected_rank:
                raise ValueError(
                    "ResearchRunRankingResult entries must have sequential ranks starting at 1."
                )
            if entry.scenario_id in entry_scenario_ids:
                raise ValueError(
                    "ResearchRunRankingResult entries cannot contain duplicate scenario IDs."
                )
            entry_scenario_ids.add(entry.scenario_id)

        excluded_scenario_ids: set[str] = set()
        for reason in normalized_excluded:
            if reason.scenario_id in excluded_scenario_ids:
                raise ValueError(
                    "ResearchRunRankingResult excluded cannot contain duplicate scenario IDs."
                )
            excluded_scenario_ids.add(reason.scenario_id)

        if entry_scenario_ids.intersection(excluded_scenario_ids):
            raise ValueError(
                "ResearchRunRankingResult cannot contain the same scenario ID in both "
                "entries and exclusions."
            )

        object.__setattr__(self, "entries", normalized_entries)
        object.__setattr__(self, "excluded", normalized_excluded)
        object.__setattr__(self, "considered_count", normalized_considered_count)

    @property
    def successful(self) -> bool:
        return self.top is not None

    @property
    def top(self) -> ResearchRunRankingEntry | None:
        if not self.entries:
            return None
        return self.entries[0]

    @property
    def selected_scenario_id(self) -> str | None:
        if self.top is None:
            return None
        return self.top.scenario_id
