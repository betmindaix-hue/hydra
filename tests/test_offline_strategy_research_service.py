from __future__ import annotations

from datetime import UTC, datetime

from hydra.application.backtesting_dto import BacktestRequest
from hydra.application.strategy_research_dto import (
    StrategyResearchRequest,
    StrategyResearchResult,
)
from hydra.application.strategy_research_service import OfflineStrategyResearchService
from hydra.domain.backtesting import BacktestDirection, ResearchSignal
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_bar(minute: int, close_price: float = 100) -> OHLCVBar:
    return OHLCVBar(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        timestamp=datetime(2026, 7, 18, 10, minute, tzinfo=UTC),
        open_price=close_price,
        high_price=close_price + 1,
        low_price=close_price - 1,
        close_price=close_price,
        volume=10,
    )


def make_series(*bars: OHLCVBar) -> MarketDataSeries:
    return MarketDataSeries(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=bars,
        source=DataSourceDescriptor(name="strategy-research-series"),
    )


class StaticStrategyResearchProvider:
    def __init__(self, signals: tuple[ResearchSignal, ...]) -> None:
        self._signals = signals
        self.last_request: StrategyResearchRequest | None = None

    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        self.last_request = request
        return self._signals


class ExplodingStrategyResearchProvider:
    def generate_signals(self, request: StrategyResearchRequest) -> tuple[ResearchSignal, ...]:
        raise RuntimeError("provider exploded")


def test_generates_research_signals_from_a_fake_provider() -> None:
    series = make_series(make_bar(0), make_bar(1))
    provider = StaticStrategyResearchProvider(
        signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.BUY,
            ),
        )
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-basic",
            market_data_series=series,
        )
    )

    assert result.successful is True
    assert len(result.signals) == 1
    assert result.signals[0].direction is BacktestDirection.BUY
    assert result.selected_bar_count == 2


def test_rejects_empty_market_data_series() -> None:
    series = MarketDataSeries(
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        bars=(),
        source=DataSourceDescriptor(name="empty-research-series"),
    )
    service = OfflineStrategyResearchService(StaticStrategyResearchProvider(signals=()))

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-empty",
            market_data_series=series,
        )
    )

    assert result.successful is False
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "market_data_series"


def test_reports_provider_errors_without_crashing() -> None:
    series = make_series(make_bar(0), make_bar(1))
    service = OfflineStrategyResearchService(ExplodingStrategyResearchProvider())

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-provider-error",
            market_data_series=series,
        )
    )

    assert result.successful is False
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "provider"
    assert "provider exploded" in result.errors[0].message


def test_rejects_signal_timestamps_not_present_in_selected_series() -> None:
    series = make_series(make_bar(0), make_bar(1), make_bar(2))
    provider = StaticStrategyResearchProvider(
        signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.BUY,
            ),
        )
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-windowed",
            market_data_series=series,
            start_timestamp=series.bars[1].timestamp,
            end_timestamp=datetime(2026, 7, 18, 10, 2, 1, tzinfo=UTC),
        )
    )

    assert result.successful is False
    assert not result.signals
    assert result.rejected_signal_count == 1
    assert result.errors[0].signal_timestamp == series.bars[0].timestamp


def test_rejects_duplicate_signal_timestamps() -> None:
    series = make_series(make_bar(0), make_bar(1))
    duplicate_timestamp = series.bars[0].timestamp
    provider = StaticStrategyResearchProvider(
        signals=(
            ResearchSignal(
                timestamp=duplicate_timestamp,
                direction=BacktestDirection.BUY,
            ),
            ResearchSignal(
                timestamp=duplicate_timestamp,
                direction=BacktestDirection.SELL,
            ),
        )
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-duplicates",
            market_data_series=series,
        )
    )

    assert len(result.signals) == 1
    assert result.rejected_signal_count == 1
    assert len(result.errors) == 1
    assert "Only one ResearchSignal is allowed per timestamp." in result.errors[0].message


def test_applies_requested_time_range() -> None:
    series = make_series(make_bar(0), make_bar(1), make_bar(2))
    provider = StaticStrategyResearchProvider(signals=())
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-range",
            market_data_series=series,
            start_timestamp=series.bars[1].timestamp,
            end_timestamp=datetime(2026, 7, 18, 10, 2, 1, tzinfo=UTC),
        )
    )

    assert result.time_range is not None
    assert result.selected_bar_count == 2
    assert provider.last_request is not None
    assert provider.last_request.start_timestamp == series.bars[1].timestamp
    assert provider.last_request.end_timestamp == datetime(2026, 7, 18, 10, 2, 1, tzinfo=UTC)


def test_keeps_hold_buy_and_sell_signals_intact() -> None:
    series = make_series(make_bar(0), make_bar(1), make_bar(2))
    provider = StaticStrategyResearchProvider(
        signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.HOLD,
            ),
            ResearchSignal(
                timestamp=series.bars[1].timestamp,
                direction=BacktestDirection.BUY,
            ),
            ResearchSignal(
                timestamp=series.bars[2].timestamp,
                direction=BacktestDirection.SELL,
            ),
        )
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-directions",
            market_data_series=series,
        )
    )

    assert result.successful is True
    assert tuple(signal.direction for signal in result.signals) == (
        BacktestDirection.HOLD,
        BacktestDirection.BUY,
        BacktestDirection.SELL,
    )


def test_returns_zero_signals_cleanly() -> None:
    series = make_series(make_bar(0), make_bar(1))
    service = OfflineStrategyResearchService(StaticStrategyResearchProvider(signals=()))

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-zero",
            market_data_series=series,
        )
    )

    assert result.successful is True
    assert not result.signals
    assert not result.errors


def test_builds_b3_backtest_request_from_valid_result() -> None:
    series = make_series(make_bar(0), make_bar(1))
    provider = StaticStrategyResearchProvider(
        signals=(
            ResearchSignal(
                timestamp=series.bars[0].timestamp,
                direction=BacktestDirection.BUY,
            ),
        )
    )
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-handoff",
            market_data_series=series,
        )
    )

    request = result.to_backtest_request(
        backtest_id="b4-to-b3",
        initial_cash=1000,
    )

    assert isinstance(request, BacktestRequest)
    assert request.research_signals == result.signals
    assert request.start_timestamp == series.bars[0].timestamp


def test_execute_does_not_run_backtest_implicitly() -> None:
    series = make_series(make_bar(0), make_bar(1))
    provider = StaticStrategyResearchProvider(signals=())
    service = OfflineStrategyResearchService(provider)

    result = service.execute(
        StrategyResearchRequest(
            research_id="b4-no-auto-backtest",
            market_data_series=series,
        )
    )

    assert isinstance(result, StrategyResearchResult)
    assert not isinstance(result, BacktestRequest)
