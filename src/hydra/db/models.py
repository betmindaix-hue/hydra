from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hydra.db.base import Base


class MarketBar(Base):
    __tablename__ = "market_bars"
    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "open_time", name="uq_market_bars_symbol_timeframe_open_time"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open_price: Mapped[float] = mapped_column(Float)
    high_price: Mapped[float] = mapped_column(Float)
    low_price: Mapped[float] = mapped_column(Float)
    close_price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(64))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    feature_sets: Mapped[list[FeatureSet]] = relationship(
        back_populates="market_bar",
        cascade="all, delete-orphan",
    )


class FeatureSet(Base):
    __tablename__ = "feature_sets"
    __table_args__ = (
        UniqueConstraint(
            "market_bar_id",
            "feature_namespace",
            "feature_version",
            name="uq_feature_sets_market_bar_id",
        ),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    market_bar_id: Mapped[str] = mapped_column(ForeignKey("market_bars.id", ondelete="CASCADE"), index=True)
    feature_namespace: Mapped[str] = mapped_column(String(64))
    feature_version: Mapped[str] = mapped_column(String(32))
    values: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    market_bar: Mapped[MarketBar] = relationship(back_populates="feature_sets")
    strategy_signals: Mapped[list[StrategySignal]] = relationship(
        back_populates="feature_set",
        cascade="all, delete-orphan",
    )


class StrategySignal(Base):
    __tablename__ = "strategy_signals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_set_id: Mapped[str] = mapped_column(ForeignKey("feature_sets.id", ondelete="CASCADE"), index=True)
    strategy_name: Mapped[str] = mapped_column(String(64), index=True)
    strategy_version: Mapped[str] = mapped_column(String(32))
    signal: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    feature_set: Mapped[FeatureSet] = relationship(back_populates="strategy_signals")
    decisions: Mapped[list[Decision]] = relationship(
        back_populates="strategy_signal",
        cascade="all, delete-orphan",
    )


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_signal_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_signals.id", ondelete="CASCADE"),
        index=True,
    )
    action: Mapped[str] = mapped_column(String(16))
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    size_fraction: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str] = mapped_column(Text)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    strategy_signal: Mapped[StrategySignal] = relationship(back_populates="decisions")
    paper_trades: Mapped[list[PaperTrade]] = relationship(
        back_populates="decision",
        cascade="all, delete-orphan",
    )


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    decision_id: Mapped[str] = mapped_column(ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    decision: Mapped[Decision] = relationship(back_populates="paper_trades")


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    equity: Mapped[float] = mapped_column(Float)
    pnl: Mapped[float] = mapped_column(Float)
    drawdown: Mapped[float] = mapped_column(Float)
    win_rate: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Experiment(Base):
    __tablename__ = "experiments"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_experiments_name_version"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(32))
    hypothesis: Mapped[str] = mapped_column(Text)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

