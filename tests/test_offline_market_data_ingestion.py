from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from hydra.application.market_data_ingestion_dto import (
    OfflineDatasetIngestionRequest,
    OfflineMarketDataRecord,
)
from hydra.application.market_data_ingestion_service import OfflineMarketDataIngestionService
from hydra.domain.market_data import DataSourceDescriptor, OHLCVBar


def make_record(**overrides: object) -> OfflineMarketDataRecord:
    payload: dict[str, object] = {
        "symbol": "btcusdt",
        "market": "spot",
        "timeframe": "1m",
        "timestamp": "2026-07-17T12:00:00+00:00",
        "open_price": "100.0",
        "high_price": "110.0",
        "low_price": "99.0",
        "close_price": "105.0",
        "volume": "42.0",
    }
    payload.update(overrides)
    return OfflineMarketDataRecord.from_mapping(payload)


class InMemoryOfflineDatasetSource:
    def __init__(
        self,
        *,
        datasets: dict[str, tuple[Mapping[str, object], ...]],
        source_name: str = "fixture source",
    ) -> None:
        self._datasets = datasets
        self._source_name = source_name
        self.describe_calls = 0
        self.list_calls = 0
        self.load_calls = 0

    def describe_source(self) -> DataSourceDescriptor:
        self.describe_calls += 1
        return DataSourceDescriptor(name=self._source_name)

    def list_available_datasets(self) -> tuple[str, ...]:
        self.list_calls += 1
        return tuple(self._datasets)

    def load_records(self, dataset_name: str) -> tuple[Mapping[str, object], ...]:
        self.load_calls += 1
        return self._datasets[dataset_name]


def test_ingests_valid_offline_records_into_series() -> None:
    service = OfflineMarketDataIngestionService()
    request = OfflineDatasetIngestionRequest(
        dataset_name="daily-bars",
        records=(
            make_record(timestamp="2026-07-17T12:00:00+00:00"),
            make_record(timestamp="2026-07-17T12:01:00+00:00"),
        ),
    )

    result = service.execute(request)

    assert result.processed_record_count == 2
    assert result.accepted_record_count == 2
    assert result.rejected_record_count == 0
    assert not result.errors
    assert len(result.series) == 1
    assert result.series[0].symbol.value == "BTCUSDT"
    assert result.series[0].market.value == "SPOT"
    assert result.series[0].timeframe.value == "1m"
    assert result.series[0].bar_count == 2
    assert result.series[0].source is not None
    assert result.series[0].source.name == "daily-bars"
    assert result.source.offline_only is True
    assert result.is_successful is True


def test_invalid_symbol_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="invalid-symbol",
            records=(make_record(symbol="   "),),
        )
    )

    assert not result.series
    assert result.accepted_record_count == 0
    assert result.rejected_record_count == 1
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "symbol"
    assert "Symbol cannot be blank" in result.errors[0].message


def test_invalid_market_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="invalid-market",
            records=(make_record(market=" "),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "market"
    assert "Market cannot be blank" in result.errors[0].message


def test_unsupported_timeframe_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="invalid-timeframe",
            records=(make_record(timeframe="2m"),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "timeframe"
    assert "Unsupported timeframe" in result.errors[0].message


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("open_price", "-1"),
        ("high_price", "-1"),
        ("low_price", "-1"),
        ("close_price", "-1"),
    ),
)
def test_negative_ohlc_prices_are_rejected_and_reported(field_name: str, value: str) -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="negative-prices",
            records=(make_record(**{field_name: value}),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == field_name
    assert "must be non-negative" in result.errors[0].message


def test_high_lower_than_low_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="bad-range",
            records=(make_record(high_price="90.0", low_price="95.0"),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "high_price"
    assert "greater than or equal to low_price" in result.errors[0].message


def test_negative_volume_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="negative-volume",
            records=(make_record(volume="-5"),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "volume"
    assert "volume must be non-negative" in result.errors[0].message


def test_naive_timestamp_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="naive-timestamp",
            records=(make_record(timestamp=datetime(2026, 7, 17, 12, 0)),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "timestamp"
    assert "timezone-aware" in result.errors[0].message


def test_unordered_records_are_reported_through_series_validation() -> None:
    service = OfflineMarketDataIngestionService()
    request = OfflineDatasetIngestionRequest(
        dataset_name="unordered-bars",
        records=(
            make_record(timestamp="2026-07-17T12:01:00+00:00"),
            make_record(timestamp="2026-07-17T12:00:00+00:00"),
        ),
    )

    result = service.execute(request)

    assert not result.series
    assert result.accepted_record_count == 0
    assert result.rejected_record_count == 2
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "bars"
    assert "strictly ordered" in result.errors[0].message


def test_mixed_symbol_records_are_grouped_explicitly() -> None:
    service = OfflineMarketDataIngestionService()
    request = OfflineDatasetIngestionRequest(
        dataset_name="mixed-symbols",
        records=(
            make_record(symbol="btcusdt"),
            make_record(
                symbol="ethusdt",
                timestamp="2026-07-17T12:02:00+00:00",
                open_price="200.0",
                high_price="210.0",
                low_price="198.0",
                close_price="205.0",
            ),
        ),
    )

    result = service.execute(request)

    assert len(result.series) == 2
    assert result.accepted_record_count == 2
    assert result.rejected_record_count == 0
    assert {series.symbol.value for series in result.series} == {"BTCUSDT", "ETHUSDT"}


def test_result_contains_validation_errors_without_stopping_valid_groups() -> None:
    service = OfflineMarketDataIngestionService()
    request = OfflineDatasetIngestionRequest(
        dataset_name="partial-batch",
        records=(
            make_record(symbol="   "),
            make_record(
                symbol="ethusdt",
                timestamp="2026-07-17T12:03:00+00:00",
            ),
        ),
    )

    result = service.execute(request)

    assert len(result.series) == 1
    assert result.accepted_record_count == 1
    assert result.rejected_record_count == 1
    assert len(result.errors) == 1
    assert result.is_successful is False


def test_service_can_load_records_through_offline_source_port() -> None:
    source = InMemoryOfflineDatasetSource(
        datasets={
            "fixture-dataset": (
                {
                    "symbol": "xrpusdt",
                    "market": "spot",
                    "timeframe": "1m",
                    "timestamp": "2026-07-17T12:00:00+00:00",
                    "open_price": "1.0",
                    "high_price": "1.1",
                    "low_price": "0.9",
                    "close_price": "1.05",
                    "volume": "5000",
                },
            )
        }
    )
    service = OfflineMarketDataIngestionService()

    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="fixture-dataset",
            source=source,
        )
    )

    assert len(result.series) == 1
    assert result.series[0].symbol.value == "XRPUSDT"
    assert result.source.name == "fixture source"
    assert source.describe_calls == 1
    assert source.list_calls == 1
    assert source.load_calls == 1


def test_direct_records_take_priority_over_source_loading() -> None:
    source = InMemoryOfflineDatasetSource(datasets={"unused": ()})
    service = OfflineMarketDataIngestionService()

    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="direct-first",
            records=(make_record(),),
            source=source,
        )
    )

    assert len(result.series) == 1
    assert source.describe_calls == 1
    assert source.list_calls == 0
    assert source.load_calls == 0


def test_record_payload_requires_all_expected_fields() -> None:
    with pytest.raises(ValueError, match="missing required fields"):
        OfflineMarketDataRecord.from_mapping({"symbol": "btcusdt"})


def test_ingestion_request_requires_records_or_source() -> None:
    with pytest.raises(ValueError, match="requires records or an offline source"):
        OfflineDatasetIngestionRequest(dataset_name="empty-request")


def test_source_dataset_must_exist_when_loading_from_port() -> None:
    source = InMemoryOfflineDatasetSource(datasets={})
    service = OfflineMarketDataIngestionService()

    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="missing-dataset",
            source=source,
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "dataset_name"
    assert result.processed_record_count == 0
    assert result.accepted_record_count == 0
    assert result.rejected_record_count == 0


def test_timestamp_string_with_z_suffix_is_normalized() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="zulu-time",
            records=(
                make_record(
                    timestamp="2026-07-17T12:00:00Z",
                    symbol="adausdt",
                    market="spot",
                ),
            ),
        )
    )

    assert len(result.series) == 1
    assert result.series[0].bars[0].timestamp == datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def test_invalid_timestamp_string_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="bad-timestamp",
            records=(make_record(timestamp="not-a-timestamp"),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "timestamp"
    assert "valid ISO 8601" in result.errors[0].message


def test_blank_numeric_strings_and_boolean_values_are_rejected() -> None:
    service = OfflineMarketDataIngestionService()

    blank_numeric_result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="blank-open",
            records=(make_record(open_price="   "),),
        )
    )
    boolean_numeric_result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="bool-volume",
            records=(make_record(volume=True),),
        )
    )

    assert len(blank_numeric_result.errors) == 1
    assert blank_numeric_result.errors[0].field_name == "open_price"
    assert "cannot be blank" in blank_numeric_result.errors[0].message
    assert len(boolean_numeric_result.errors) == 1
    assert boolean_numeric_result.errors[0].field_name == "volume"
    assert "must be numeric" in boolean_numeric_result.errors[0].message


def test_non_string_timeframe_is_rejected_and_reported() -> None:
    service = OfflineMarketDataIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="integer-timeframe",
            records=(make_record(timeframe=1),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "timeframe"
    assert "timeframe must be a string" in result.errors[0].message


def test_source_payload_validation_errors_are_reported_without_loading_invalid_records() -> None:
    source = InMemoryOfflineDatasetSource(
        datasets={
            "fixture-dataset": (
                {
                    "symbol": "xrpusdt",
                    "market": "spot",
                    "timeframe": "1m",
                    "timestamp": "2026-07-17T12:00:00+00:00",
                    "open_price": "1.0",
                    "high_price": "1.1",
                    "low_price": "0.9",
                    "close_price": "1.05",
                    "volume": "5000",
                },
                {"symbol": "xrpusdt"},
            )
        }
    )
    service = OfflineMarketDataIngestionService()

    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="fixture-dataset",
            source=source,
        )
    )

    assert len(result.series) == 1
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "record"
    assert "missing required fields" in result.errors[0].message


def test_unknown_validation_message_keeps_field_name_empty() -> None:
    class FailingIngestionService(OfflineMarketDataIngestionService):
        def _build_bar(self, record: OfflineMarketDataRecord) -> OHLCVBar:
            del record
            raise ValueError("unexpected validation failure")

    service = FailingIngestionService()
    result = service.execute(
        OfflineDatasetIngestionRequest(
            dataset_name="unknown-field",
            records=(make_record(),),
        )
    )

    assert not result.series
    assert len(result.errors) == 1
    assert result.errors[0].field_name is None
