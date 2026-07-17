from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hydra.domain.market_data import (
    DataQualityIssue,
    DataQualityIssueType,
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


def make_bar(
    *,
    timestamp: datetime,
    symbol: Symbol | None = None,
    market: Market | None = None,
    timeframe: Timeframe = Timeframe.MINUTE_1,
    open_price: float = 100.0,
    high_price: float = 105.0,
    low_price: float = 99.0,
    close_price: float = 102.0,
    volume: float = 10.0,
) -> OHLCVBar:
    return OHLCVBar(
        symbol=symbol or Symbol("btcusdt"),
        market=market or Market("spot"),
        timeframe=timeframe,
        timestamp=timestamp,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
    )


def test_symbol_creation_normalizes_value() -> None:
    symbol = Symbol("  btcusdt  ")

    assert symbol.value == "BTCUSDT"
    assert str(symbol) == "BTCUSDT"


def test_symbol_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        Symbol("   ")


def test_market_creation_normalizes_value() -> None:
    market = Market("  spot  ")

    assert market.value == "SPOT"
    assert str(market) == "SPOT"


def test_market_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        Market("")


def test_timeframe_accepts_supported_value() -> None:
    timeframe = Timeframe("1h")

    assert timeframe is Timeframe.HOUR_1


def test_timeframe_rejects_unsupported_value() -> None:
    with pytest.raises(ValueError):
        Timeframe("2m")


def test_ohlcv_bar_accepts_valid_values() -> None:
    timestamp = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

    bar = make_bar(timestamp=timestamp)

    assert bar.timestamp == timestamp
    assert bar.volume == 10.0


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("open_price", -1.0),
        ("high_price", -1.0),
        ("low_price", -1.0),
        ("close_price", -1.0),
    ),
)
def test_ohlcv_bar_rejects_negative_prices(field_name: str, value: float) -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        if field_name == "open_price":
            make_bar(
                timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
                open_price=value,
            )
        elif field_name == "high_price":
            make_bar(
                timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
                high_price=value,
            )
        elif field_name == "low_price":
            make_bar(
                timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
                low_price=value,
            )
        else:
            make_bar(
                timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
                close_price=value,
            )


def test_ohlcv_bar_rejects_negative_volume() -> None:
    with pytest.raises(ValueError, match="volume must be non-negative"):
        make_bar(
            timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            volume=-1.0,
        )


def test_ohlcv_bar_rejects_inverted_high_low() -> None:
    with pytest.raises(ValueError, match="greater than or equal to low_price"):
        make_bar(
            timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            high_price=90.0,
            low_price=95.0,
        )


def test_ohlcv_bar_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        make_bar(timestamp=datetime(2026, 7, 17, 12, 0))


def test_market_data_series_accepts_ordered_bars() -> None:
    symbol = Symbol("ethusdt")
    market = Market("spot")
    bars = (
        make_bar(
            symbol=symbol,
            market=market,
            timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
        ),
        make_bar(
            symbol=symbol,
            market=market,
            timestamp=datetime(2026, 7, 17, 12, 1, tzinfo=UTC),
        ),
    )

    series = MarketDataSeries(
        symbol=symbol,
        market=market,
        timeframe=Timeframe.MINUTE_1,
        bars=bars,
    )

    assert series.bar_count == 2


def test_market_data_series_rejects_unordered_bars() -> None:
    symbol = Symbol("ethusdt")
    market = Market("spot")
    later_timestamp = datetime(2026, 7, 17, 12, 1, tzinfo=UTC)
    earlier_timestamp = later_timestamp - timedelta(minutes=1)

    with pytest.raises(ValueError, match="strictly ordered"):
        MarketDataSeries(
            symbol=symbol,
            market=market,
            timeframe=Timeframe.MINUTE_1,
            bars=(
                make_bar(symbol=symbol, market=market, timestamp=later_timestamp),
                make_bar(symbol=symbol, market=market, timestamp=earlier_timestamp),
            ),
        )


def test_market_data_series_rejects_bar_metadata_mismatches() -> None:
    symbol = Symbol("ethusdt")
    market = Market("spot")

    with pytest.raises(ValueError, match="same market as the series"):
        MarketDataSeries(
            symbol=symbol,
            market=market,
            timeframe=Timeframe.MINUTE_1,
            bars=(
                make_bar(
                    symbol=symbol,
                    market=Market("futures"),
                    timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
                ),
            ),
        )


def test_data_quality_issue_representation_is_clear() -> None:
    issue = DataQualityIssue(
        issue_type=DataQualityIssueType.DUPLICATE_TIMESTAMP,
        message="duplicate timestamp detected",
        timestamp=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
    )

    assert issue.message == "duplicate timestamp detected"
    assert str(issue) == "duplicate_timestamp: duplicate timestamp detected"


def test_data_source_descriptor_representation_defaults_to_offline_first() -> None:
    issue = DataQualityIssue(
        issue_type=DataQualityIssueType.GAP,
        message="missing one expected bar",
    )

    descriptor = DataSourceDescriptor(
        name="daily parquet import",
        quality_issues=(issue,),
    )

    assert descriptor.offline_only is True
    assert descriptor.quality_issues == (issue,)
    assert str(descriptor) == "daily parquet import [offline-only]"


def test_data_source_descriptor_rejects_mixed_mode_configuration() -> None:
    with pytest.raises(ValueError, match="offline-only in B1"):
        DataSourceDescriptor(
            name="unexpected mixed mode import",
            offline_only=False,
        )
