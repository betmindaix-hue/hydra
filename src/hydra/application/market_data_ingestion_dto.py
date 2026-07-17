from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

from hydra.domain.market_data import DataSourceDescriptor, MarketDataSeries
from hydra.ports.offline_dataset import OfflineDatasetSourcePort

type RawTimestamp = datetime | str
type RawNumeric = float | int | str

_REQUIRED_RECORD_FIELDS = (
    "symbol",
    "market",
    "timeframe",
    "timestamp",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
)


@dataclass(frozen=True, slots=True)
class OfflineMarketDataRecord:
    symbol: str
    market: str
    timeframe: str
    timestamp: RawTimestamp
    open_price: RawNumeric
    high_price: RawNumeric
    low_price: RawNumeric
    close_price: RawNumeric
    volume: RawNumeric

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> OfflineMarketDataRecord:
        missing_fields = tuple(
            field_name for field_name in _REQUIRED_RECORD_FIELDS if field_name not in payload
        )
        if missing_fields:
            raise ValueError(
                "Offline market data record payload is missing required fields: "
                + ", ".join(missing_fields)
            )

        return cls(
            symbol=cast(str, payload["symbol"]),
            market=cast(str, payload["market"]),
            timeframe=cast(str, payload["timeframe"]),
            timestamp=cast(RawTimestamp, payload["timestamp"]),
            open_price=cast(RawNumeric, payload["open_price"]),
            high_price=cast(RawNumeric, payload["high_price"]),
            low_price=cast(RawNumeric, payload["low_price"]),
            close_price=cast(RawNumeric, payload["close_price"]),
            volume=cast(RawNumeric, payload["volume"]),
        )


@dataclass(frozen=True, slots=True)
class OfflineDatasetIngestionRequest:
    dataset_name: str
    records: tuple[OfflineMarketDataRecord, ...] = field(default_factory=tuple)
    source: OfflineDatasetSourcePort | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_name, str) or not self.dataset_name.strip():
            raise ValueError("Offline dataset ingestion request requires a dataset name.")

        if self.source is None and not self.records:
            raise ValueError(
                "Offline dataset ingestion request requires records or an offline source."
            )

        object.__setattr__(self, "dataset_name", self.dataset_name.strip())


@dataclass(frozen=True, slots=True)
class OfflineDatasetIngestionError:
    dataset_name: str
    message: str
    record_index: int | None = None
    field_name: str | None = None
    raw_record: OfflineMarketDataRecord | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_name, str) or not self.dataset_name.strip():
            raise ValueError("Offline dataset ingestion error requires a dataset name.")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("Offline dataset ingestion error requires a message.")
        if self.field_name is not None and not self.field_name.strip():
            raise ValueError("Offline dataset ingestion error field_name cannot be blank.")

        object.__setattr__(self, "dataset_name", self.dataset_name.strip())
        object.__setattr__(self, "message", self.message.strip())
        if self.field_name is not None:
            object.__setattr__(self, "field_name", self.field_name.strip())


@dataclass(frozen=True, slots=True)
class OfflineDatasetIngestionResult:
    dataset_name: str
    source: DataSourceDescriptor
    series: tuple[MarketDataSeries, ...] = field(default_factory=tuple)
    errors: tuple[OfflineDatasetIngestionError, ...] = field(default_factory=tuple)
    processed_record_count: int = 0
    accepted_record_count: int = 0
    rejected_record_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_name, str) or not self.dataset_name.strip():
            raise ValueError("Offline dataset ingestion result requires a dataset name.")

        counts = (
            self.processed_record_count,
            self.accepted_record_count,
            self.rejected_record_count,
        )
        if any(count < 0 for count in counts):
            raise ValueError("Offline dataset ingestion counts must be non-negative.")
        if self.accepted_record_count + self.rejected_record_count != self.processed_record_count:
            raise ValueError(
                "accepted_record_count and rejected_record_count must add up to "
                "processed_record_count."
            )

        object.__setattr__(self, "dataset_name", self.dataset_name.strip())

    @property
    def is_successful(self) -> bool:
        return self.accepted_record_count > 0 and not self.errors
