from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Timeframe(StrEnum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"


@dataclass(frozen=True, slots=True)
class Symbol:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("Symbol must be a string.")

        normalized = self.value.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be blank.")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Market:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("Market must be a string.")

        normalized = self.value.strip().upper()
        if not normalized:
            raise ValueError("Market cannot be blank.")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class OHLCVBar:
    symbol: Symbol
    market: Market
    timeframe: Timeframe
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("OHLCV bar timestamp must be timezone-aware.")

        for field_name in ("open_price", "high_price", "low_price", "close_price"):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative.")

        if self.high_price < self.low_price:
            raise ValueError("high_price must be greater than or equal to low_price.")

        if self.volume < 0:
            raise ValueError("volume must be non-negative.")


class DataQualityIssueType(StrEnum):
    DUPLICATE_TIMESTAMP = "duplicate_timestamp"
    GAP = "gap"
    MISSING_DATA = "missing_data"
    OUTLIER = "outlier"
    STALE_SOURCE = "stale_source"


@dataclass(frozen=True, slots=True)
class DataQualityIssue:
    issue_type: DataQualityIssueType
    message: str
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("Data quality issue message cannot be blank.")

        if self.timestamp is not None and (
            self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None
        ):
            raise ValueError("Data quality issue timestamp must be timezone-aware.")

        object.__setattr__(self, "message", self.message.strip())

    def __str__(self) -> str:
        return f"{self.issue_type.value}: {self.message}"


@dataclass(frozen=True, slots=True)
class DataSourceDescriptor:
    name: str
    offline_only: bool = True
    quality_issues: tuple[DataQualityIssue, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Data source name cannot be blank.")
        if self.offline_only is not True:
            raise ValueError("Data source descriptors must remain offline-only in B1.")

        object.__setattr__(self, "name", self.name.strip())

    def __str__(self) -> str:
        return f"{self.name} [offline-only]"


@dataclass(frozen=True, slots=True)
class MarketDataSeries:
    symbol: Symbol
    market: Market
    timeframe: Timeframe
    bars: tuple[OHLCVBar, ...] = field(default_factory=tuple)
    source: DataSourceDescriptor | None = None

    def __post_init__(self) -> None:
        previous_timestamp: datetime | None = None

        for bar in self.bars:
            if bar.symbol != self.symbol:
                raise ValueError("All bars must use the same symbol as the series.")
            if bar.market != self.market:
                raise ValueError("All bars must use the same market as the series.")
            if bar.timeframe is not self.timeframe:
                raise ValueError("All bars must use the same timeframe as the series.")
            if previous_timestamp is not None and bar.timestamp <= previous_timestamp:
                raise ValueError("Market data series bars must be strictly ordered by timestamp.")
            previous_timestamp = bar.timestamp

    @property
    def bar_count(self) -> int:
        return len(self.bars)
