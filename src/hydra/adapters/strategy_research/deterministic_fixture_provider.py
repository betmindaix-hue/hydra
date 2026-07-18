from __future__ import annotations

from dataclasses import dataclass

from hydra.application.strategy_research_dto import StrategyResearchRequest
from hydra.domain.backtesting import BacktestDirection, ResearchSignal
from hydra.domain.market_data import OHLCVBar


@dataclass(frozen=True, slots=True)
class FixtureSignalInstruction:
    bar_index: int
    direction: BacktestDirection
    note: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.bar_index, bool) or not isinstance(self.bar_index, int):
            raise ValueError("FixtureSignalInstruction bar_index must be an integer.")
        if self.bar_index < 0:
            raise ValueError("FixtureSignalInstruction bar_index must be non-negative.")
        if not isinstance(self.direction, BacktestDirection):
            raise ValueError("FixtureSignalInstruction direction must be a BacktestDirection.")
        if self.note is not None:
            if not isinstance(self.note, str):
                raise ValueError("FixtureSignalInstruction note must be a string when provided.")
            normalized_note = self.note.strip()
            object.__setattr__(self, "note", normalized_note or None)


class DeterministicFixtureStrategyResearchProvider:
    def __init__(self, instructions: tuple[FixtureSignalInstruction, ...] = ()) -> None:
        resolved_instructions = tuple(instructions)
        seen_bar_indexes: set[int] = set()
        normalized_instructions: list[FixtureSignalInstruction] = []

        for instruction in resolved_instructions:
            if not isinstance(instruction, FixtureSignalInstruction):
                raise ValueError(
                    "DeterministicFixtureStrategyResearchProvider instructions must "
                    "contain only FixtureSignalInstruction values."
                )
            if instruction.bar_index in seen_bar_indexes:
                raise ValueError("FixtureSignalInstruction bar_index values must be unique.")

            seen_bar_indexes.add(instruction.bar_index)
            normalized_instructions.append(instruction)

        normalized_instructions.sort(key=lambda instruction: instruction.bar_index)
        self._instructions = tuple(normalized_instructions)

    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        selected_bars = self._select_bars(request)
        signals: list[ResearchSignal] = []

        for instruction in self._instructions:
            if instruction.bar_index >= len(selected_bars):
                raise ValueError(
                    "FixtureSignalInstruction bar_index "
                    f"{instruction.bar_index} is outside the selected bar window "
                    f"of {len(selected_bars)} bars."
                )

            selected_bar = selected_bars[instruction.bar_index]
            signals.append(
                ResearchSignal(
                    timestamp=selected_bar.timestamp,
                    direction=instruction.direction,
                    note=instruction.note,
                )
            )

        return tuple(signals)

    def _select_bars(self, request: StrategyResearchRequest) -> tuple[OHLCVBar, ...]:
        return tuple(
            bar for bar in request.market_data_series.bars if self._is_inside_window(bar, request)
        )

    def _is_inside_window(self, bar: OHLCVBar, request: StrategyResearchRequest) -> bool:
        if request.start_timestamp is not None and bar.timestamp < request.start_timestamp:
            return False
        if request.end_timestamp is not None and bar.timestamp > request.end_timestamp:
            return False
        return True
