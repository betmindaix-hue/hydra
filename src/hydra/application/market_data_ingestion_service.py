from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from hydra.application.market_data_ingestion_dto import (
    OfflineDatasetIngestionError,
    OfflineDatasetIngestionRequest,
    OfflineDatasetIngestionResult,
    OfflineMarketDataRecord,
)
from hydra.domain.market_data import (
    DataSourceDescriptor,
    Market,
    MarketDataSeries,
    OHLCVBar,
    Symbol,
    Timeframe,
)


class OfflineMarketDataIngestionService:
    def execute(self, request: OfflineDatasetIngestionRequest) -> OfflineDatasetIngestionResult:
        source = self._resolve_source_descriptor(request)
        records, errors = self._resolve_records(request)
        grouped_bars: dict[tuple[Symbol, Market, Timeframe], list[OHLCVBar]] = {}

        for index, record in enumerate(records):
            try:
                bar = self._build_bar(record)
            except ValueError as exc:
                errors.append(
                    OfflineDatasetIngestionError(
                        dataset_name=request.dataset_name,
                        record_index=index,
                        field_name=self._infer_field_name(str(exc)),
                        message=str(exc),
                        raw_record=record,
                    )
                )
                continue

            key = (bar.symbol, bar.market, bar.timeframe)
            grouped_bars.setdefault(key, []).append(bar)

        series_collection: list[MarketDataSeries] = []
        accepted_record_count = 0

        for (symbol, market, timeframe), bars in grouped_bars.items():
            try:
                series = MarketDataSeries(
                    symbol=symbol,
                    market=market,
                    timeframe=timeframe,
                    bars=tuple(bars),
                    source=source,
                )
            except ValueError as exc:
                errors.append(
                    OfflineDatasetIngestionError(
                        dataset_name=request.dataset_name,
                        field_name="bars",
                        message=(
                            f"Series validation failed for "
                            f"{symbol.value}/{market.value}/{timeframe.value}: {exc}"
                        ),
                    )
                )
                continue

            series_collection.append(series)
            accepted_record_count += series.bar_count

        processed_record_count = len(records)
        return OfflineDatasetIngestionResult(
            dataset_name=request.dataset_name,
            source=source,
            series=tuple(series_collection),
            errors=tuple(errors),
            processed_record_count=processed_record_count,
            accepted_record_count=accepted_record_count,
            rejected_record_count=processed_record_count - accepted_record_count,
        )

    def _resolve_source_descriptor(
        self, request: OfflineDatasetIngestionRequest
    ) -> DataSourceDescriptor:
        if request.source is not None:
            return request.source.describe_source()
        return DataSourceDescriptor(name=request.dataset_name)

    def _resolve_records(
        self, request: OfflineDatasetIngestionRequest
    ) -> tuple[tuple[OfflineMarketDataRecord, ...], list[OfflineDatasetIngestionError]]:
        if request.records:
            return request.records, []

        if request.source is None:
            return (), []

        available_datasets = request.source.list_available_datasets()
        if request.dataset_name not in available_datasets:
            return (
                (),
                [
                    OfflineDatasetIngestionError(
                        dataset_name=request.dataset_name,
                        field_name="dataset_name",
                        message=(
                            "Offline dataset source does not expose the requested dataset: "
                            f"{request.dataset_name}"
                        ),
                    )
                ],
            )

        resolved_records: list[OfflineMarketDataRecord] = []
        errors: list[OfflineDatasetIngestionError] = []

        for index, payload in enumerate(request.source.load_records(request.dataset_name)):
            try:
                resolved_records.append(self._record_from_payload(payload))
            except ValueError as exc:
                errors.append(
                    OfflineDatasetIngestionError(
                        dataset_name=request.dataset_name,
                        record_index=index,
                        field_name="record",
                        message=str(exc),
                    )
                )

        return tuple(resolved_records), errors

    def _record_from_payload(self, payload: Mapping[str, object]) -> OfflineMarketDataRecord:
        return OfflineMarketDataRecord.from_mapping(payload)

    def _build_bar(self, record: OfflineMarketDataRecord) -> OHLCVBar:
        return OHLCVBar(
            symbol=Symbol(record.symbol),
            market=Market(record.market),
            timeframe=self._normalize_timeframe(record.timeframe),
            timestamp=self._normalize_timestamp(record.timestamp),
            open_price=self._normalize_numeric(record.open_price, "open_price"),
            high_price=self._normalize_numeric(record.high_price, "high_price"),
            low_price=self._normalize_numeric(record.low_price, "low_price"),
            close_price=self._normalize_numeric(record.close_price, "close_price"),
            volume=self._normalize_numeric(record.volume, "volume"),
        )

    def _normalize_timeframe(self, timeframe: str) -> Timeframe:
        if isinstance(timeframe, Timeframe):
            return timeframe
        if not isinstance(timeframe, str):
            raise ValueError("timeframe must be a string.")

        try:
            return Timeframe(timeframe.strip())
        except ValueError as exc:
            raise ValueError(f"Unsupported timeframe: {timeframe}") from exc

    def _normalize_timestamp(self, timestamp: datetime | str) -> datetime:
        if isinstance(timestamp, datetime):
            return timestamp
        if not isinstance(timestamp, str):
            raise ValueError("timestamp must be a datetime or ISO 8601 string.")

        normalized = timestamp.strip()
        if not normalized:
            raise ValueError("timestamp cannot be blank.")
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            return datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"timestamp must be a valid ISO 8601 value: {timestamp}") from exc

    def _normalize_numeric(self, value: float | int | str, field_name: str) -> float:
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be numeric.")
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be numeric.")

        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} cannot be blank.")

        try:
            return float(normalized)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be numeric.") from exc

    def _infer_field_name(self, message: str) -> str | None:
        lowered_message = message.lower()
        for field_name in (
            "symbol",
            "market",
            "timeframe",
            "timestamp",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
        ):
            if field_name in lowered_message:
                return field_name
        return None
