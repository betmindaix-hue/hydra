from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType

from hydra.application.backtesting_dto import BacktestRequest
from hydra.domain.backtesting import BacktestTimeRange, ResearchSignal
from hydra.domain.market_data import MarketDataSeries

type StrategyParameterValue = str | int | float | bool | None


def _normalize_parameters(
    parameters: Mapping[str, StrategyParameterValue],
) -> Mapping[str, StrategyParameterValue]:
    resolved_parameters: dict[str, StrategyParameterValue] = {}

    for key, value in parameters.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("StrategyResearchRequest parameter keys cannot be blank.")
        if isinstance(value, (list, tuple, dict, set)):
            raise ValueError("StrategyResearchRequest parameter values must be simple primitives.")
        if not isinstance(value, (str, int, float, bool)) and value is not None:
            raise ValueError("StrategyResearchRequest parameter values must be simple primitives.")

        resolved_parameters[key.strip()] = value

    return MappingProxyType(resolved_parameters)


@dataclass(frozen=True, slots=True)
class StrategyResearchRequest:
    research_id: str
    market_data_series: MarketDataSeries
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    parameters: Mapping[str, StrategyParameterValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.research_id, str) or not self.research_id.strip():
            raise ValueError("StrategyResearchRequest research_id cannot be blank.")

        if self.start_timestamp is not None and (
            self.start_timestamp.tzinfo is None or self.start_timestamp.utcoffset() is None
        ):
            raise ValueError("StrategyResearchRequest start_timestamp must be timezone-aware.")
        if self.end_timestamp is not None and (
            self.end_timestamp.tzinfo is None or self.end_timestamp.utcoffset() is None
        ):
            raise ValueError("StrategyResearchRequest end_timestamp must be timezone-aware.")
        if (
            self.start_timestamp is not None
            and self.end_timestamp is not None
            and self.start_timestamp >= self.end_timestamp
        ):
            raise ValueError(
                "StrategyResearchRequest start_timestamp must be before end_timestamp."
            )

        object.__setattr__(self, "research_id", self.research_id.strip())
        object.__setattr__(self, "parameters", _normalize_parameters(self.parameters))

    def with_time_range(
        self,
        *,
        start_timestamp: datetime,
        end_timestamp: datetime,
    ) -> StrategyResearchRequest:
        return StrategyResearchRequest(
            research_id=self.research_id,
            market_data_series=self.market_data_series,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            parameters=self.parameters,
        )


@dataclass(frozen=True, slots=True)
class StrategyResearchError:
    message: str
    field_name: str | None = None
    signal_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("StrategyResearchError message cannot be blank.")
        if self.field_name is not None and not self.field_name.strip():
            raise ValueError("StrategyResearchError field_name cannot be blank.")
        if self.signal_timestamp is not None and (
            self.signal_timestamp.tzinfo is None or self.signal_timestamp.utcoffset() is None
        ):
            raise ValueError("StrategyResearchError signal_timestamp must be timezone-aware.")

        object.__setattr__(self, "message", self.message.strip())
        if self.field_name is not None:
            object.__setattr__(self, "field_name", self.field_name.strip())


@dataclass(frozen=True, slots=True)
class StrategyResearchResult:
    research_id: str
    market_data_series: MarketDataSeries
    time_range: BacktestTimeRange | None = None
    signals: tuple[ResearchSignal, ...] = field(default_factory=tuple)
    errors: tuple[StrategyResearchError, ...] = field(default_factory=tuple)
    selected_bar_count: int = 0
    rejected_signal_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.research_id, str) or not self.research_id.strip():
            raise ValueError("StrategyResearchResult research_id cannot be blank.")
        if self.selected_bar_count < 0:
            raise ValueError("StrategyResearchResult selected_bar_count must be non-negative.")
        if self.rejected_signal_count < 0:
            raise ValueError("StrategyResearchResult rejected_signal_count must be non-negative.")

        object.__setattr__(self, "research_id", self.research_id.strip())

    @property
    def successful(self) -> bool:
        return not self.errors

    def to_backtest_request(self, *, backtest_id: str, initial_cash: float) -> BacktestRequest:
        if self.errors:
            raise ValueError("StrategyResearchResult must be error-free before backtest handoff.")
        if self.time_range is None:
            raise ValueError("StrategyResearchResult time_range is required for backtest handoff.")

        return BacktestRequest(
            backtest_id=backtest_id,
            market_data_series=self.market_data_series,
            initial_cash=initial_cash,
            research_signals=self.signals,
            start_timestamp=self.time_range.start,
            end_timestamp=self.time_range.end,
        )
