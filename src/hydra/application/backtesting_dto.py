from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from hydra.domain.backtesting import BacktestResult, ResearchSignal
from hydra.domain.market_data import MarketDataSeries


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    backtest_id: str
    market_data_series: MarketDataSeries
    initial_cash: float
    research_signals: tuple[ResearchSignal, ...] = field(default_factory=tuple)
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.backtest_id, str) or not self.backtest_id.strip():
            raise ValueError("BacktestRequest backtest_id cannot be blank.")
        if self.start_timestamp is not None and (
            self.start_timestamp.tzinfo is None or self.start_timestamp.utcoffset() is None
        ):
            raise ValueError("BacktestRequest start_timestamp must be timezone-aware.")
        if self.end_timestamp is not None and (
            self.end_timestamp.tzinfo is None or self.end_timestamp.utcoffset() is None
        ):
            raise ValueError("BacktestRequest end_timestamp must be timezone-aware.")

        object.__setattr__(self, "backtest_id", self.backtest_id.strip())


@dataclass(frozen=True, slots=True)
class BacktestValidationError:
    message: str
    field_name: str | None = None
    signal_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("BacktestValidationError message cannot be blank.")
        if self.field_name is not None and not self.field_name.strip():
            raise ValueError("BacktestValidationError field_name cannot be blank.")
        if self.signal_timestamp is not None and (
            self.signal_timestamp.tzinfo is None or self.signal_timestamp.utcoffset() is None
        ):
            raise ValueError("BacktestValidationError signal_timestamp must be timezone-aware.")

        object.__setattr__(self, "message", self.message.strip())
        if self.field_name is not None:
            object.__setattr__(self, "field_name", self.field_name.strip())


@dataclass(frozen=True, slots=True)
class BacktestRunSummary:
    backtest_id: str
    result: BacktestResult | None = None
    errors: tuple[BacktestValidationError, ...] = field(default_factory=tuple)
    processed_bar_count: int = 0
    simulated_trade_count: int = 0
    ignored_signal_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.backtest_id, str) or not self.backtest_id.strip():
            raise ValueError("BacktestRunSummary backtest_id cannot be blank.")

        for field_name in ("processed_bar_count", "simulated_trade_count", "ignored_signal_count"):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"BacktestRunSummary {field_name} must be non-negative.")

        object.__setattr__(self, "backtest_id", self.backtest_id.strip())

    @property
    def successful(self) -> bool:
        return self.result is not None and not self.errors
