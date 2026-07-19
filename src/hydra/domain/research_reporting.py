from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from hydra.domain.backtesting import BacktestId, BacktestTimeRange
from hydra.domain.market_data import DataSourceDescriptor, Market, Symbol, Timeframe


def _normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")

    normalized = value.strip()
    return normalized or None


def _normalize_notes(notes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(notes, str):
        raise ValueError("ResearchReport notes must be an iterable of strings.")

    normalized_notes: list[str] = []
    for note in notes:
        if not isinstance(note, str):
            raise ValueError("ResearchReport notes must contain only strings.")

        normalized = note.strip()
        if normalized:
            normalized_notes.append(normalized)

    return tuple(normalized_notes)


def _require_timezone_aware(timestamp: datetime, *, field_name: str) -> None:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _require_number(value: float, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number.")


def _require_count(value: int, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")


@dataclass(frozen=True, slots=True)
class ResearchReportId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("ResearchReportId must be a string.")

        normalized = self.value.strip()
        if not normalized:
            raise ValueError("ResearchReportId cannot be blank.")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    initial_cash: float
    ending_cash: float
    ending_equity: float
    total_return: float
    max_drawdown: float
    trade_count: int
    signal_count: int

    def __post_init__(self) -> None:
        for field_name in ("initial_cash", "ending_cash", "ending_equity", "total_return"):
            _require_number(getattr(self, field_name), field_name=field_name)

        for field_name in ("trade_count", "signal_count"):
            _require_count(getattr(self, field_name), field_name=field_name)

        if self.initial_cash <= 0:
            raise ValueError("MetricSnapshot initial_cash must be positive.")
        if self.ending_cash < 0:
            raise ValueError("MetricSnapshot ending_cash must be non-negative.")
        if self.ending_equity < 0:
            raise ValueError("MetricSnapshot ending_equity must be non-negative.")
        if self.total_return < -1:
            raise ValueError("MetricSnapshot total_return cannot be less than -1.")
        if not 0 <= self.max_drawdown <= 1:
            raise ValueError("MetricSnapshot max_drawdown must stay between 0 and 1.")
        if self.trade_count < 0:
            raise ValueError("MetricSnapshot trade_count must be non-negative.")
        if self.signal_count < 0:
            raise ValueError("MetricSnapshot signal_count must be non-negative.")


@dataclass(frozen=True, slots=True)
class EquityCurveSummary:
    point_count: int
    first_timestamp: datetime
    last_timestamp: datetime
    starting_equity: float
    ending_equity: float
    min_equity: float
    max_equity: float
    lowest_cash: float
    highest_position_quantity: float

    def __post_init__(self) -> None:
        _require_count(self.point_count, field_name="point_count")
        if self.point_count <= 0:
            raise ValueError("EquityCurveSummary point_count must be positive.")

        _require_timezone_aware(self.first_timestamp, field_name="first_timestamp")
        _require_timezone_aware(self.last_timestamp, field_name="last_timestamp")
        if self.first_timestamp > self.last_timestamp:
            raise ValueError(
                "EquityCurveSummary first_timestamp must be before or equal to last_timestamp."
            )

        for field_name in (
            "starting_equity",
            "ending_equity",
            "min_equity",
            "max_equity",
            "lowest_cash",
            "highest_position_quantity",
        ):
            value = getattr(self, field_name)
            _require_number(value, field_name=field_name)
            if value < 0:
                raise ValueError(f"EquityCurveSummary {field_name} must be non-negative.")

        if self.min_equity > self.max_equity:
            raise ValueError("EquityCurveSummary min_equity cannot exceed max_equity.")


@dataclass(frozen=True, slots=True)
class SignalSummary:
    backtest_signal_count: int
    research_signal_count: int | None = None
    rejected_signal_count: int | None = None
    research_error_count: int | None = None
    buy_signal_count: int | None = None
    sell_signal_count: int | None = None
    hold_signal_count: int | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "backtest_signal_count",
            "research_signal_count",
            "rejected_signal_count",
            "research_error_count",
            "buy_signal_count",
            "sell_signal_count",
            "hold_signal_count",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue

            _require_count(value, field_name=field_name)
            if value < 0:
                raise ValueError(f"SignalSummary {field_name} must be non-negative.")


@dataclass(frozen=True, slots=True)
class SimulatedTradeSummary:
    trade_count: int
    buy_count: int
    sell_count: int
    first_trade_timestamp: datetime | None = None
    last_trade_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("trade_count", "buy_count", "sell_count"):
            value = getattr(self, field_name)
            _require_count(value, field_name=field_name)
            if value < 0:
                raise ValueError(f"SimulatedTradeSummary {field_name} must be non-negative.")

        if self.buy_count + self.sell_count != self.trade_count:
            raise ValueError(
                "SimulatedTradeSummary buy_count and sell_count must equal trade_count."
            )

        if self.trade_count == 0:
            if self.first_trade_timestamp is not None or self.last_trade_timestamp is not None:
                raise ValueError(
                    "SimulatedTradeSummary timestamps must be None when trade_count is 0."
                )
            return

        if self.first_trade_timestamp is None or self.last_trade_timestamp is None:
            raise ValueError(
                "SimulatedTradeSummary timestamps are required when trade_count is positive."
            )

        _require_timezone_aware(
            self.first_trade_timestamp,
            field_name="first_trade_timestamp",
        )
        _require_timezone_aware(
            self.last_trade_timestamp,
            field_name="last_trade_timestamp",
        )
        if self.first_trade_timestamp > self.last_trade_timestamp:
            raise ValueError(
                "SimulatedTradeSummary first_trade_timestamp must be before or equal to "
                "last_trade_timestamp."
            )


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    max_drawdown: float
    total_return: float
    final_position_open: bool
    final_position_quantity: float
    final_position_average_entry_price: float

    def __post_init__(self) -> None:
        for field_name in (
            "max_drawdown",
            "total_return",
            "final_position_quantity",
            "final_position_average_entry_price",
        ):
            _require_number(getattr(self, field_name), field_name=field_name)

        if not 0 <= self.max_drawdown <= 1:
            raise ValueError("RiskSnapshot max_drawdown must stay between 0 and 1.")
        if self.total_return < -1:
            raise ValueError("RiskSnapshot total_return cannot be less than -1.")
        if self.final_position_quantity < 0:
            raise ValueError("RiskSnapshot final_position_quantity must be non-negative.")
        if self.final_position_average_entry_price < 0:
            raise ValueError(
                "RiskSnapshot final_position_average_entry_price must be non-negative."
            )
        if not self.final_position_open and self.final_position_quantity != 0:
            raise ValueError(
                "RiskSnapshot final_position_quantity must be 0 when final_position_open is False."
            )


@dataclass(frozen=True, slots=True)
class ResearchReport:
    report_id: ResearchReportId
    title: str | None
    backtest_id: BacktestId
    symbol: Symbol
    market: Market
    timeframe: Timeframe
    time_range: BacktestTimeRange
    source: DataSourceDescriptor | None
    metrics: MetricSnapshot
    equity_curve: EquityCurveSummary
    signals: SignalSummary
    simulated_trades: SimulatedTradeSummary
    risk: RiskSnapshot
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.report_id, ResearchReportId):
            raise ValueError("ResearchReport report_id must be a ResearchReportId.")
        if not isinstance(self.backtest_id, BacktestId):
            raise ValueError("ResearchReport backtest_id must be a BacktestId.")
        if not isinstance(self.metrics, MetricSnapshot):
            raise ValueError("ResearchReport metrics must be a MetricSnapshot.")
        if not isinstance(self.equity_curve, EquityCurveSummary):
            raise ValueError("ResearchReport equity_curve must be an EquityCurveSummary.")
        if not isinstance(self.signals, SignalSummary):
            raise ValueError("ResearchReport signals must be a SignalSummary.")
        if not isinstance(self.simulated_trades, SimulatedTradeSummary):
            raise ValueError("ResearchReport simulated_trades must be a SimulatedTradeSummary.")
        if not isinstance(self.risk, RiskSnapshot):
            raise ValueError("ResearchReport risk must be a RiskSnapshot.")

        object.__setattr__(
            self,
            "title",
            _normalize_optional_text(self.title, field_name="ResearchReport title"),
        )
        object.__setattr__(self, "notes", _normalize_notes(self.notes))
