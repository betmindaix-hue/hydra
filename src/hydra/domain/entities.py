from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MarketBar:
    id: UUID
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    source: str
    raw_payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class FeatureSet:
    id: UUID
    market_bar_id: UUID
    feature_namespace: str
    feature_version: str
    values: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class StrategySignal:
    id: UUID
    feature_set_id: UUID
    strategy_name: str
    strategy_version: str
    signal: str
    confidence: float
    explanation: str
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    id: UUID
    strategy_signal_id: UUID
    action: str
    approved: bool = False
    size_fraction: float = 0.0
    rationale: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PaperTrade:
    id: UUID
    decision_id: UUID
    symbol: str
    side: str
    quantity: float
    entry_price: float
    status: str
    exit_price: float | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    id: UUID
    as_of: datetime
    equity: float
    pnl: float
    drawdown: float
    win_rate: float
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Pattern:
    id: UUID
    name: str
    description: str
    conditions: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Experiment:
    id: UUID
    name: str
    version: str
    hypothesis: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
