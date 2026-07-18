from __future__ import annotations

from datetime import datetime, timedelta

from hydra.application.strategy_research_dto import (
    StrategyResearchError,
    StrategyResearchRequest,
    StrategyResearchResult,
)
from hydra.domain.backtesting import BacktestTimeRange, ResearchSignal
from hydra.domain.market_data import MarketDataSeries, OHLCVBar
from hydra.ports.strategy_research import StrategyResearchProviderPort


class OfflineStrategyResearchService:
    def __init__(self, provider: StrategyResearchProviderPort) -> None:
        self._provider = provider

    def execute(self, request: StrategyResearchRequest) -> StrategyResearchResult:
        errors: list[StrategyResearchError] = []

        if not request.market_data_series.bars:
            errors.append(
                StrategyResearchError(
                    message=(
                        "StrategyResearchRequest market_data_series must contain at least one bar."
                    ),
                    field_name="market_data_series",
                )
            )
            return StrategyResearchResult(
                research_id=request.research_id,
                market_data_series=request.market_data_series,
                errors=tuple(errors),
            )

        try:
            time_range = self._resolve_time_range(request.market_data_series, request)
        except ValueError as exc:
            errors.append(StrategyResearchError(message=str(exc), field_name="time_range"))
            return StrategyResearchResult(
                research_id=request.research_id,
                market_data_series=request.market_data_series,
                errors=tuple(errors),
            )

        selected_bars = tuple(
            bar
            for bar in request.market_data_series.bars
            if time_range.start <= bar.timestamp <= time_range.end
        )
        if not selected_bars:
            errors.append(
                StrategyResearchError(
                    message="No market data bars remain inside the requested research time range.",
                    field_name="market_data_series",
                )
            )
            return StrategyResearchResult(
                research_id=request.research_id,
                market_data_series=request.market_data_series,
                time_range=time_range,
                errors=tuple(errors),
            )

        provider_request = request.with_time_range(
            start_timestamp=time_range.start,
            end_timestamp=time_range.end,
        )

        try:
            generated_signals = self._provider.generate_signals(provider_request)
        except Exception as exc:
            errors.append(
                StrategyResearchError(
                    message=f"Strategy research provider failed: {exc}",
                    field_name="provider",
                )
            )
            return StrategyResearchResult(
                research_id=request.research_id,
                market_data_series=request.market_data_series,
                time_range=time_range,
                errors=tuple(errors),
                selected_bar_count=len(selected_bars),
            )

        signals, rejected_signal_count = self._validate_signals(
            generated_signals,
            selected_bars,
            errors,
        )
        return StrategyResearchResult(
            research_id=request.research_id,
            market_data_series=request.market_data_series,
            time_range=time_range,
            signals=signals,
            errors=tuple(errors),
            selected_bar_count=len(selected_bars),
            rejected_signal_count=rejected_signal_count,
        )

    def _resolve_time_range(
        self,
        series: MarketDataSeries,
        request: StrategyResearchRequest,
    ) -> BacktestTimeRange:
        series_start = series.bars[0].timestamp
        series_end = series.bars[-1].timestamp

        effective_start = request.start_timestamp or series_start
        effective_end = request.end_timestamp or self._default_time_range_end(
            series_start,
            series_end,
        )
        return BacktestTimeRange(start=effective_start, end=effective_end)

    def _default_time_range_end(
        self,
        series_start: datetime,
        series_end: datetime,
    ) -> datetime:
        if series_start < series_end:
            return series_end
        return series_end + timedelta(microseconds=1)

    def _validate_signals(
        self,
        generated_signals: tuple[ResearchSignal, ...],
        selected_bars: tuple[OHLCVBar, ...],
        errors: list[StrategyResearchError],
    ) -> tuple[tuple[ResearchSignal, ...], int]:
        selected_timestamps = {bar.timestamp for bar in selected_bars}
        accepted_signals: list[ResearchSignal] = []
        seen_timestamps: set[datetime] = set()
        rejected_signal_count = 0

        for signal in generated_signals:
            if signal.timestamp not in selected_timestamps:
                errors.append(
                    StrategyResearchError(
                        message=(
                            "ResearchSignal timestamp does not exist in the selected "
                            "offline market data series."
                        ),
                        field_name="signals",
                        signal_timestamp=signal.timestamp,
                    )
                )
                rejected_signal_count += 1
                continue

            if signal.timestamp in seen_timestamps:
                errors.append(
                    StrategyResearchError(
                        message="Only one ResearchSignal is allowed per timestamp.",
                        field_name="signals",
                        signal_timestamp=signal.timestamp,
                    )
                )
                rejected_signal_count += 1
                continue

            seen_timestamps.add(signal.timestamp)
            accepted_signals.append(signal)

        return tuple(accepted_signals), rejected_signal_count
