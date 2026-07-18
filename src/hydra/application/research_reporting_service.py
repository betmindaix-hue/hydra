from __future__ import annotations

from hydra.application.research_reporting_dto import (
    ResearchReportGenerationError,
    ResearchReportGenerationResult,
    ResearchReportRequest,
)
from hydra.application.strategy_research_dto import StrategyResearchResult
from hydra.domain.backtesting import BacktestDirection, BacktestResult, SimulatedTrade
from hydra.domain.research_reporting import (
    EquityCurveSummary,
    MetricSnapshot,
    ResearchReport,
    ResearchReportId,
    RiskSnapshot,
    SignalSummary,
    SimulatedTradeSummary,
)


class OfflineResearchReportingService:
    def generate(self, request: object) -> ResearchReportGenerationResult:
        if not isinstance(request, ResearchReportRequest):
            return ResearchReportGenerationResult(
                errors=(
                    ResearchReportGenerationError(
                        message="ResearchReportRequest is required.",
                        field_name="request",
                    ),
                )
            )

        try:
            strategy_research_result = request.strategy_research_result
            if strategy_research_result is not None:
                self._validate_strategy_research_alignment(
                    request.backtest_result,
                    strategy_research_result,
                )

            report = ResearchReport(
                report_id=ResearchReportId(request.report_id),
                title=request.title,
                backtest_id=request.backtest_result.backtest_id,
                symbol=request.backtest_result.symbol,
                market=request.backtest_result.market,
                timeframe=request.backtest_result.timeframe,
                time_range=request.backtest_result.time_range,
                source=request.backtest_result.source,
                metrics=self._build_metric_snapshot(request.backtest_result),
                equity_curve=self._build_equity_curve_summary(request.backtest_result),
                signals=self._build_signal_summary(
                    request.backtest_result,
                    strategy_research_result,
                ),
                simulated_trades=self._build_trade_summary(request.backtest_result),
                risk=self._build_risk_snapshot(request.backtest_result),
                notes=request.notes,
            )
        except ValueError as exc:
            field_name = "report"
            if "strategy research result" in str(exc).lower():
                field_name = "strategy_research_result"

            return ResearchReportGenerationResult(
                errors=(
                    ResearchReportGenerationError(
                        message=str(exc),
                        field_name=field_name,
                    ),
                )
            )

        return ResearchReportGenerationResult(report=report)

    def _build_metric_snapshot(self, backtest_result: BacktestResult) -> MetricSnapshot:
        metrics = backtest_result.metrics
        if metrics is None:
            raise ValueError("BacktestResult metrics are required for research reporting.")

        return MetricSnapshot(
            initial_cash=metrics.initial_cash,
            ending_cash=metrics.ending_cash,
            ending_equity=metrics.ending_equity,
            total_return=metrics.total_return,
            max_drawdown=metrics.max_drawdown,
            trade_count=metrics.trade_count,
            signal_count=backtest_result.signal_count,
        )

    def _build_equity_curve_summary(self, backtest_result: BacktestResult) -> EquityCurveSummary:
        first_point = backtest_result.equity_curve[0]
        last_point = backtest_result.equity_curve[-1]

        return EquityCurveSummary(
            point_count=len(backtest_result.equity_curve),
            first_timestamp=first_point.timestamp,
            last_timestamp=last_point.timestamp,
            starting_equity=first_point.equity,
            ending_equity=last_point.equity,
            min_equity=min(point.equity for point in backtest_result.equity_curve),
            max_equity=max(point.equity for point in backtest_result.equity_curve),
            lowest_cash=min(point.cash for point in backtest_result.equity_curve),
            highest_position_quantity=max(
                point.position_quantity for point in backtest_result.equity_curve
            ),
        )

    def _build_signal_summary(
        self,
        backtest_result: BacktestResult,
        strategy_research_result: StrategyResearchResult | None,
    ) -> SignalSummary:
        if strategy_research_result is None:
            return SignalSummary(backtest_signal_count=backtest_result.signal_count)

        buy_signal_count = 0
        sell_signal_count = 0
        hold_signal_count = 0

        for signal in strategy_research_result.signals:
            if signal.direction is BacktestDirection.BUY:
                buy_signal_count += 1
            elif signal.direction is BacktestDirection.SELL:
                sell_signal_count += 1
            else:
                hold_signal_count += 1

        return SignalSummary(
            backtest_signal_count=backtest_result.signal_count,
            research_signal_count=len(strategy_research_result.signals),
            rejected_signal_count=strategy_research_result.rejected_signal_count,
            research_error_count=len(strategy_research_result.errors),
            buy_signal_count=buy_signal_count,
            sell_signal_count=sell_signal_count,
            hold_signal_count=hold_signal_count,
        )

    def _build_trade_summary(self, backtest_result: BacktestResult) -> SimulatedTradeSummary:
        simulated_trades = backtest_result.simulated_trades
        if not simulated_trades:
            return SimulatedTradeSummary(
                trade_count=0,
                buy_count=0,
                sell_count=0,
            )

        return SimulatedTradeSummary(
            trade_count=len(simulated_trades),
            buy_count=self._count_trades(simulated_trades, BacktestDirection.BUY),
            sell_count=self._count_trades(simulated_trades, BacktestDirection.SELL),
            first_trade_timestamp=simulated_trades[0].timestamp,
            last_trade_timestamp=simulated_trades[-1].timestamp,
        )

    def _build_risk_snapshot(self, backtest_result: BacktestResult) -> RiskSnapshot:
        metrics = backtest_result.metrics
        if metrics is None:
            raise ValueError("BacktestResult metrics are required for research reporting.")

        final_position = backtest_result.final_position
        return RiskSnapshot(
            max_drawdown=metrics.max_drawdown,
            total_return=metrics.total_return,
            final_position_open=final_position.is_open,
            final_position_quantity=final_position.quantity,
            final_position_average_entry_price=final_position.average_entry_price,
        )

    def _count_trades(
        self,
        simulated_trades: tuple[SimulatedTrade, ...],
        direction: BacktestDirection,
    ) -> int:
        return sum(1 for trade in simulated_trades if trade.direction is direction)

    def _validate_strategy_research_alignment(
        self,
        backtest_result: BacktestResult,
        strategy_research_result: StrategyResearchResult,
    ) -> None:
        series = strategy_research_result.market_data_series
        if series.symbol != backtest_result.symbol:
            raise ValueError("Strategy research result symbol must match BacktestResult symbol.")
        if series.market != backtest_result.market:
            raise ValueError("Strategy research result market must match BacktestResult market.")
        if series.timeframe is not backtest_result.timeframe:
            raise ValueError(
                "Strategy research result timeframe must match BacktestResult timeframe."
            )
