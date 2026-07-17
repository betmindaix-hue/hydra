from __future__ import annotations

from typing import Protocol, runtime_checkable

from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    Symbol,
    Timeframe,
)


@runtime_checkable
class OfflineMarketDataRepositoryPort(Protocol):
    def list_available_symbols(self, market: Market) -> tuple[Symbol, ...]:
        """List symbols available for an offline market segment."""

    def get_series(
        self,
        symbol: Symbol,
        market: Market,
        timeframe: Timeframe,
    ) -> MarketDataSeries | None:
        """Return a previously stored offline series when available."""

    def save_bars(
        self,
        series: MarketDataSeries,
        source: DataSourceDescriptor,
    ) -> None:
        """Persist an offline series without implying live connectivity."""


@runtime_checkable
class OfflineMarketDataSourcePort(Protocol):
    def describe_source(self) -> DataSourceDescriptor:
        """Describe an offline source without exposing implementation details."""

    def list_available_symbols(self, market: Market) -> tuple[Symbol, ...]:
        """List symbols discoverable from an offline source."""

    def load_bars(
        self,
        symbol: Symbol,
        market: Market,
        timeframe: Timeframe,
    ) -> MarketDataSeries:
        """Load a normalized offline series for a symbol, market, and timeframe."""
