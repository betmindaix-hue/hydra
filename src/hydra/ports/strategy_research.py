from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from hydra.domain.backtesting import ResearchSignal

if TYPE_CHECKING:
    from hydra.application.strategy_research_dto import StrategyResearchRequest


@runtime_checkable
class StrategyResearchProviderPort(Protocol):
    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        """Generate offline research signals without implying live execution or external IO."""
