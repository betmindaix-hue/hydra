from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from hydra.domain.market_data import DataSourceDescriptor


@runtime_checkable
class OfflineDatasetSourcePort(Protocol):
    def describe_source(self) -> DataSourceDescriptor:
        """Describe an offline dataset source without exposing implementation details."""

    def list_available_datasets(self) -> tuple[str, ...]:
        """List dataset identifiers available from an offline source."""

    def load_records(self, dataset_name: str) -> tuple[Mapping[str, object], ...]:
        """Load raw offline records for a named dataset without implying external IO."""
