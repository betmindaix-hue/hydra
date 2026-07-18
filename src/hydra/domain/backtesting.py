from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from hydra.domain.market_data import DataSourceDescriptor, Market, Symbol, Timeframe


class BacktestDirection(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True, slots=True)
class BacktestId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("BacktestId must be a string.")

        normalized = self.value.strip()
        if not normalized:
            raise ValueError("BacktestId cannot be blank.")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class BacktestTimeRange:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        for field_name in ("start", "end"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"BacktestTimeRange {field_name} must be timezone-aware.")

        if self.start >= self.end:
            raise ValueError("BacktestTimeRange start must be before end.")

    def contains(self, timestamp: datetime) -> bool:
        return self.start <= timestamp <= self.end


@dataclass(frozen=True, slots=True)
class ResearchSignal:
    timestamp: datetime
    direction: BacktestDirection
    note: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("ResearchSignal timestamp must be timezone-aware.")
        if not isinstance(self.direction, BacktestDirection):
            raise ValueError("ResearchSignal direction must be a BacktestDirection.")
        if self.note is not None:
            normalized = self.note.strip()
            object.__setattr__(self, "note", normalized or None)


@dataclass(frozen=True, slots=True)
class SimulatedTrade:
    timestamp: datetime
    direction: BacktestDirection
    quantity: float
    price: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("SimulatedTrade timestamp must be timezone-aware.")
        if self.direction is BacktestDirection.HOLD:
            raise ValueError("SimulatedTrade direction cannot be HOLD.")
        if self.quantity <= 0:
            raise ValueError("SimulatedTrade quantity must be positive.")
        if self.price < 0:
            raise ValueError("SimulatedTrade price must be non-negative.")


@dataclass(frozen=True, slots=True)
class SimulatedPosition:
    quantity: float = 0.0
    average_entry_price: float = 0.0
    opened_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("SimulatedPosition quantity must be non-negative.")
        if self.average_entry_price < 0:
            raise ValueError("SimulatedPosition average_entry_price must be non-negative.")

        if self.quantity == 0:
            if self.average_entry_price != 0:
                raise ValueError(
                    "SimulatedPosition average_entry_price must be 0 when quantity is 0."
                )
            if self.opened_at is not None:
                raise ValueError("SimulatedPosition opened_at must be None when quantity is 0.")
            return

        if self.average_entry_price == 0:
            raise ValueError(
                "SimulatedPosition average_entry_price must be positive when quantity is open."
            )
        if self.opened_at is None:
            raise ValueError("SimulatedPosition opened_at is required when quantity is open.")
        if self.opened_at.tzinfo is None or self.opened_at.utcoffset() is None:
            raise ValueError("SimulatedPosition opened_at must be timezone-aware.")

    @property
    def is_open(self) -> bool:
        return self.quantity > 0


@dataclass(frozen=True, slots=True)
class EquityCurvePoint:
    timestamp: datetime
    equity: float
    cash: float
    position_quantity: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("EquityCurvePoint timestamp must be timezone-aware.")
        if self.equity < 0:
            raise ValueError("EquityCurvePoint equity must be non-negative.")
        if self.cash < 0:
            raise ValueError("EquityCurvePoint cash must be non-negative.")
        if self.position_quantity < 0:
            raise ValueError("EquityCurvePoint position_quantity must be non-negative.")


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    initial_cash: float
    ending_cash: float
    ending_equity: float
    total_return: float
    max_drawdown: float
    trade_count: int

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("BacktestMetrics initial_cash must be positive.")
        if self.ending_cash < 0:
            raise ValueError("BacktestMetrics ending_cash must be non-negative.")
        if self.ending_equity < 0:
            raise ValueError("BacktestMetrics ending_equity must be non-negative.")
        if self.total_return < -1:
            raise ValueError("BacktestMetrics total_return cannot be less than -1.")
        if not 0 <= self.max_drawdown <= 1:
            raise ValueError("BacktestMetrics max_drawdown must stay between 0 and 1.")
        if self.trade_count < 0:
            raise ValueError("BacktestMetrics trade_count must be non-negative.")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    backtest_id: BacktestId
    symbol: Symbol
    market: Market
    timeframe: Timeframe
    time_range: BacktestTimeRange
    source: DataSourceDescriptor | None
    simulated_trades: tuple[SimulatedTrade, ...] = field(default_factory=tuple)
    equity_curve: tuple[EquityCurvePoint, ...] = field(default_factory=tuple)
    metrics: BacktestMetrics | None = None
    final_position: SimulatedPosition = field(default_factory=SimulatedPosition)
    signal_count: int = 0

    def __post_init__(self) -> None:
        if not self.equity_curve:
            raise ValueError("BacktestResult must include at least one equity curve point.")
        if self.metrics is None:
            raise ValueError("BacktestResult metrics are required.")
        if self.signal_count < 0:
            raise ValueError("BacktestResult signal_count must be non-negative.")
