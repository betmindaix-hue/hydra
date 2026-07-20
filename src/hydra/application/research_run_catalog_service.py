from __future__ import annotations

from hydra.application.offline_research_scenario_dto import OfflineResearchScenarioResult
from hydra.application.research_run_catalog_dto import (
    ResearchRunCatalogAddResult,
    ResearchRunCatalogError,
    ResearchRunCatalogQuery,
    ResearchRunComparisonSummary,
    ResearchRunRecord,
    ResearchRunStatus,
)


def _normalize_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string.")
    return value.strip()


class InMemoryResearchRunCatalog:
    def __init__(self) -> None:
        self._records: dict[str, ResearchRunRecord] = {}

    def add_result(
        self,
        scenario_result: OfflineResearchScenarioResult,
        *,
        title: str | None = None,
        notes: tuple[str, ...] = (),
        replace_existing: bool = False,
    ) -> ResearchRunCatalogAddResult:
        if not isinstance(replace_existing, bool):
            return ResearchRunCatalogAddResult(
                errors=(
                    ResearchRunCatalogError(
                        message="replace_existing must be a bool.",
                        field_name="replace_existing",
                    ),
                )
            )

        if not isinstance(scenario_result, OfflineResearchScenarioResult):
            return ResearchRunCatalogAddResult(
                errors=(
                    ResearchRunCatalogError(
                        message=("scenario_result must be an OfflineResearchScenarioResult."),
                        field_name="scenario_result",
                    ),
                )
            )

        scenario_id = scenario_result.scenario_id
        if scenario_id in self._records and not replace_existing:
            return ResearchRunCatalogAddResult(
                errors=(
                    ResearchRunCatalogError(
                        message=(
                            "InMemoryResearchRunCatalog already contains the scenario_id: "
                            f"{scenario_id}"
                        ),
                        field_name="scenario_id",
                        scenario_id=scenario_id,
                    ),
                )
            )

        status = (
            ResearchRunStatus.SUCCESSFUL if scenario_result.successful else ResearchRunStatus.FAILED
        )
        try:
            record = ResearchRunRecord(
                scenario_id=scenario_id,
                status=status,
                scenario_result=scenario_result,
                title=title,
                notes=notes,
            )
        except ValueError as exc:
            return ResearchRunCatalogAddResult(
                errors=(
                    ResearchRunCatalogError(
                        message=str(exc),
                        scenario_id=scenario_id,
                    ),
                )
            )

        self._records[record.scenario_id] = record
        return ResearchRunCatalogAddResult(record=record)

    def get(self, scenario_id: str) -> ResearchRunRecord | None:
        normalized_scenario_id = _normalize_identifier(
            scenario_id,
            field_name="InMemoryResearchRunCatalog get scenario_id",
        )
        return self._records.get(normalized_scenario_id)

    def list(
        self,
        query: ResearchRunCatalogQuery | None = None,
    ) -> tuple[ResearchRunRecord, ...]:
        if query is None:
            return tuple(self._records.values())
        if not isinstance(query, ResearchRunCatalogQuery):
            raise ValueError(
                "InMemoryResearchRunCatalog list query must be a ResearchRunCatalogQuery "
                "when provided."
            )

        return tuple(
            record for record in self._records.values() if self._matches_query(record, query)
        )

    def compare(
        self,
        query: ResearchRunCatalogQuery | None = None,
    ) -> ResearchRunComparisonSummary:
        records = self.list(query)
        successful_run_count = 0
        failed_run_count = 0
        best_total_return_record: ResearchRunRecord | None = None
        lowest_max_drawdown_record: ResearchRunRecord | None = None
        highest_trade_count_record: ResearchRunRecord | None = None

        for record in records:
            if record.successful:
                successful_run_count += 1
            else:
                failed_run_count += 1

            total_return = record.total_return
            best_total_return = (
                None if best_total_return_record is None else best_total_return_record.total_return
            )
            if total_return is not None and (
                best_total_return is None or total_return > best_total_return
            ):
                best_total_return_record = record

            max_drawdown = record.max_drawdown
            lowest_max_drawdown = (
                None
                if lowest_max_drawdown_record is None
                else lowest_max_drawdown_record.max_drawdown
            )
            if max_drawdown is not None and (
                lowest_max_drawdown is None or max_drawdown < lowest_max_drawdown
            ):
                lowest_max_drawdown_record = record

            trade_count = record.trade_count
            highest_trade_count = (
                None
                if highest_trade_count_record is None
                else highest_trade_count_record.trade_count
            )
            if trade_count is not None and (
                highest_trade_count is None or trade_count > highest_trade_count
            ):
                highest_trade_count_record = record

        return ResearchRunComparisonSummary(
            run_count=len(records),
            successful_run_count=successful_run_count,
            failed_run_count=failed_run_count,
            best_total_return_scenario_id=(
                None if best_total_return_record is None else best_total_return_record.scenario_id
            ),
            best_total_return=(
                None if best_total_return_record is None else best_total_return_record.total_return
            ),
            lowest_max_drawdown_scenario_id=(
                None
                if lowest_max_drawdown_record is None
                else lowest_max_drawdown_record.scenario_id
            ),
            lowest_max_drawdown=(
                None
                if lowest_max_drawdown_record is None
                else lowest_max_drawdown_record.max_drawdown
            ),
            highest_trade_count_scenario_id=(
                None
                if highest_trade_count_record is None
                else highest_trade_count_record.scenario_id
            ),
            highest_trade_count=(
                None
                if highest_trade_count_record is None
                else highest_trade_count_record.trade_count
            ),
        )

    def _matches_query(
        self,
        record: ResearchRunRecord,
        query: ResearchRunCatalogQuery,
    ) -> bool:
        if query.status is not None and record.status is not query.status:
            return False
        if query.symbol is not None and record.symbol != query.symbol:
            return False
        if query.market is not None and record.market != query.market:
            return False
        if query.timeframe is not None and record.timeframe != query.timeframe:
            return False
        if query.require_report and not record.has_report:
            return False
        if query.require_backtest and not record.has_backtest:
            return False
        return True
