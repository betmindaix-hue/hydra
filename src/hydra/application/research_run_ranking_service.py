from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from hydra.application.research_run_catalog_dto import ResearchRunRecord
from hydra.application.research_run_ranking_dto import (
    ResearchRunEligibilityCriteria,
    ResearchRunExclusionReason,
    ResearchRunRankingDirection,
    ResearchRunRankingEntry,
    ResearchRunRankingMetric,
    ResearchRunRankingResult,
    ResearchRunRankingSpec,
)


@dataclass(frozen=True, slots=True)
class _RankingCandidate:
    record: ResearchRunRecord
    metric_value: float | int
    insertion_index: int


class ResearchRunRankingService:
    def rank(
        self,
        records: Iterable[ResearchRunRecord],
        spec: ResearchRunRankingSpec,
    ) -> ResearchRunRankingResult:
        normalized_records = self._normalize_records(records)
        if not isinstance(spec, ResearchRunRankingSpec):
            raise ValueError("ResearchRunRankingService spec must be a ResearchRunRankingSpec.")

        excluded: list[ResearchRunExclusionReason] = []
        candidates: list[_RankingCandidate] = []

        for insertion_index, record in enumerate(normalized_records):
            exclusion_reason = self._evaluate_eligibility(record, spec.eligibility)
            if exclusion_reason is not None:
                excluded.append(exclusion_reason)
                continue

            metric_value = self._extract_metric_value(record, spec.metric)
            if metric_value is None:
                excluded.append(
                    ResearchRunExclusionReason(
                        scenario_id=record.scenario_id,
                        reason="missing metric",
                        field_name=spec.metric.value,
                    )
                )
                continue

            candidates.append(
                _RankingCandidate(
                    record=record,
                    metric_value=metric_value,
                    insertion_index=insertion_index,
                )
            )

        sorted_candidates = self._sort_candidates(
            candidates,
            direction=spec.resolved_direction,
        )
        limited_candidates = (
            sorted_candidates if spec.limit is None else sorted_candidates[: spec.limit]
        )
        entries = tuple(
            ResearchRunRankingEntry(
                rank=rank,
                scenario_id=candidate.record.scenario_id,
                record=candidate.record,
                metric=spec.metric,
                metric_value=candidate.metric_value,
                insertion_index=candidate.insertion_index,
            )
            for rank, candidate in enumerate(limited_candidates, start=1)
        )
        return ResearchRunRankingResult(
            entries=entries,
            excluded=tuple(excluded),
            considered_count=len(normalized_records),
        )

    def select_best(
        self,
        records: Iterable[ResearchRunRecord],
        spec: ResearchRunRankingSpec,
    ) -> ResearchRunRankingEntry | None:
        return self.rank(records, spec).top

    def _normalize_records(
        self,
        records: Iterable[ResearchRunRecord],
    ) -> tuple[ResearchRunRecord, ...]:
        if isinstance(records, (str, bytes)):
            raise ValueError(
                "ResearchRunRankingService records must be an iterable of "
                "ResearchRunRecord values."
            )

        try:
            normalized_records = tuple(records)
        except TypeError as exc:
            raise ValueError(
                "ResearchRunRankingService records must be an iterable of "
                "ResearchRunRecord values."
            ) from exc

        for record in normalized_records:
            if not isinstance(record, ResearchRunRecord):
                raise ValueError(
                    "ResearchRunRankingService records must contain only "
                    "ResearchRunRecord values."
                )

        return normalized_records

    def _evaluate_eligibility(
        self,
        record: ResearchRunRecord,
        criteria: ResearchRunEligibilityCriteria,
    ) -> ResearchRunExclusionReason | None:
        if criteria.status is not None and record.status is not criteria.status:
            return ResearchRunExclusionReason(
                scenario_id=record.scenario_id,
                reason="status mismatch",
                field_name="status",
            )
        if criteria.symbol is not None and record.symbol != criteria.symbol:
            return ResearchRunExclusionReason(
                scenario_id=record.scenario_id,
                reason="symbol mismatch",
                field_name="symbol",
            )
        if criteria.market is not None and record.market != criteria.market:
            return ResearchRunExclusionReason(
                scenario_id=record.scenario_id,
                reason="market mismatch",
                field_name="market",
            )
        if criteria.timeframe is not None and record.timeframe != criteria.timeframe:
            return ResearchRunExclusionReason(
                scenario_id=record.scenario_id,
                reason="timeframe mismatch",
                field_name="timeframe",
            )
        if criteria.require_report and not record.has_report:
            return ResearchRunExclusionReason(
                scenario_id=record.scenario_id,
                reason="missing report",
                field_name="report",
            )
        if criteria.require_backtest and not record.has_backtest:
            return ResearchRunExclusionReason(
                scenario_id=record.scenario_id,
                reason="missing backtest",
                field_name="backtest",
            )

        threshold_checks = (
            (
                "total_return",
                record.total_return,
                criteria.min_total_return,
                criteria.max_total_return,
            ),
            (
                "max_drawdown",
                record.max_drawdown,
                criteria.min_max_drawdown,
                criteria.max_max_drawdown,
            ),
            (
                "trade_count",
                record.trade_count,
                criteria.min_trade_count,
                criteria.max_trade_count,
            ),
            (
                "signal_count",
                record.signal_count,
                criteria.min_signal_count,
                criteria.max_signal_count,
            ),
        )
        for field_name, value, minimum, maximum in threshold_checks:
            threshold_failure = self._evaluate_threshold(
                scenario_id=record.scenario_id,
                field_name=field_name,
                value=value,
                minimum=minimum,
                maximum=maximum,
            )
            if threshold_failure is not None:
                return threshold_failure

        return None

    def _evaluate_threshold(
        self,
        *,
        scenario_id: str,
        field_name: str,
        value: float | int | None,
        minimum: float | int | None,
        maximum: float | int | None,
    ) -> ResearchRunExclusionReason | None:
        if minimum is None and maximum is None:
            return None
        if value is None:
            return ResearchRunExclusionReason(
                scenario_id=scenario_id,
                reason="missing metric",
                field_name=field_name,
            )
        if minimum is not None and value < minimum:
            return ResearchRunExclusionReason(
                scenario_id=scenario_id,
                reason="below minimum threshold",
                field_name=field_name,
            )
        if maximum is not None and value > maximum:
            return ResearchRunExclusionReason(
                scenario_id=scenario_id,
                reason="above maximum threshold",
                field_name=field_name,
            )
        return None

    def _extract_metric_value(
        self,
        record: ResearchRunRecord,
        metric: ResearchRunRankingMetric,
    ) -> float | int | None:
        if metric is ResearchRunRankingMetric.TOTAL_RETURN:
            return record.total_return
        if metric is ResearchRunRankingMetric.MAX_DRAWDOWN:
            return record.max_drawdown
        if metric is ResearchRunRankingMetric.TRADE_COUNT:
            return record.trade_count
        return record.signal_count

    def _sort_candidates(
        self,
        candidates: list[_RankingCandidate],
        *,
        direction: ResearchRunRankingDirection,
    ) -> list[_RankingCandidate]:
        if direction is ResearchRunRankingDirection.HIGHER_FIRST:
            return sorted(
                candidates,
                key=lambda candidate: (
                    -float(candidate.metric_value),
                    candidate.insertion_index,
                ),
            )

        return sorted(
            candidates,
            key=lambda candidate: (
                float(candidate.metric_value),
                candidate.insertion_index,
            ),
        )
