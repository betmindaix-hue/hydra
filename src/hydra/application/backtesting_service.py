from __future__ import annotations

from datetime import datetime, timedelta

from hydra.application.backtesting_dto import (
    BacktestRequest,
    BacktestRunSummary,
    BacktestValidationError,
)
from hydra.domain.backtesting import (
    BacktestDirection,
    BacktestId,
    BacktestMetrics,
    BacktestResult,
    BacktestTimeRange,
    EquityCurvePoint,
    ResearchSignal,
    SimulatedPosition,
    SimulatedTrade,
)
from hydra.domain.market_data import MarketDataSeries, OHLCVBar


class OfflineBacktestingService:
    def execute(self, request: BacktestRequest) -> BacktestRunSummary:
        errors: list[BacktestValidationError] = []

        try:
            backtest_id = BacktestId(request.backtest_id)
        except ValueError as exc:
            errors.append(BacktestValidationError(message=str(exc), field_name="backtest_id"))
            return BacktestRunSummary(backtest_id=request.backtest_id, errors=tuple(errors))

        if request.initial_cash <= 0:
            errors.append(
                BacktestValidationError(
                    message="BacktestRequest initial_cash must be positive.",
                    field_name="initial_cash",
                )
            )
            return BacktestRunSummary(backtest_id=backtest_id.value, errors=tuple(errors))

        if not request.market_data_series.bars:
            errors.append(
                BacktestValidationError(
                    message="BacktestRequest market_data_series must contain at least one bar.",
                    field_name="market_data_series",
                )
            )
            return BacktestRunSummary(backtest_id=backtest_id.value, errors=tuple(errors))

        try:
            time_range = self._resolve_time_range(request.market_data_series, request)
        except ValueError as exc:
            errors.append(BacktestValidationError(message=str(exc), field_name="time_range"))
            return BacktestRunSummary(backtest_id=backtest_id.value, errors=tuple(errors))

        bars = tuple(
            bar
            for bar in request.market_data_series.bars
            if time_range.start <= bar.timestamp <= time_range.end
        )
        if not bars:
            errors.append(
                BacktestValidationError(
                    message="No market data bars remain inside the requested backtest time range.",
                    field_name="market_data_series",
                )
            )
            return BacktestRunSummary(backtest_id=backtest_id.value, errors=tuple(errors))

        signals, ignored_signal_count = self._filter_signals(
            request.research_signals,
            bars,
            errors,
        )
        result = self._simulate(
            backtest_id,
            request.market_data_series,
            bars,
            time_range,
            request,
            signals,
            errors,
        )
        return BacktestRunSummary(
            backtest_id=backtest_id.value,
            result=result,
            errors=tuple(errors),
            processed_bar_count=len(bars),
            simulated_trade_count=len(result.simulated_trades),
            ignored_signal_count=ignored_signal_count,
        )

    def _resolve_time_range(
        self, series: MarketDataSeries, request: BacktestRequest
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

    def _filter_signals(
        self,
        research_signals: tuple[ResearchSignal, ...],
        bars: tuple[OHLCVBar, ...],
        errors: list[BacktestValidationError],
    ) -> tuple[dict[datetime, ResearchSignal], int]:
        timestamps = {bar.timestamp for bar in bars}
        resolved_signals: dict[datetime, ResearchSignal] = {}
        ignored_signal_count = 0

        for signal in research_signals:
            if signal.timestamp not in timestamps:
                errors.append(
                    BacktestValidationError(
                        message=(
                            "ResearchSignal timestamp does not exist in the selected "
                            "offline market data series."
                        ),
                        field_name="research_signals",
                        signal_timestamp=signal.timestamp,
                    )
                )
                ignored_signal_count += 1
                continue

            if signal.timestamp in resolved_signals:
                errors.append(
                    BacktestValidationError(
                        message="Only one ResearchSignal is allowed per timestamp.",
                        field_name="research_signals",
                        signal_timestamp=signal.timestamp,
                    )
                )
                ignored_signal_count += 1
                continue

            resolved_signals[signal.timestamp] = signal

        return resolved_signals, ignored_signal_count

    def _simulate(
        self,
        backtest_id: BacktestId,
        series: MarketDataSeries,
        bars: tuple[OHLCVBar, ...],
        time_range: BacktestTimeRange,
        request: BacktestRequest,
        signals: dict[datetime, ResearchSignal],
        errors: list[BacktestValidationError],
    ) -> BacktestResult:
        cash = float(request.initial_cash)
        position = SimulatedPosition()
        simulated_trades: list[SimulatedTrade] = []
        equity_curve: list[EquityCurvePoint] = []

        for bar in bars:
            signal = signals.get(bar.timestamp)
            if signal is not None:
                cash, position = self._apply_signal(
                    signal,
                    bar,
                    cash,
                    position,
                    simulated_trades,
                    errors,
                )

            equity = cash + (position.quantity * bar.close_price)
            equity_curve.append(
                EquityCurvePoint(
                    timestamp=bar.timestamp,
                    equity=equity,
                    cash=cash,
                    position_quantity=position.quantity,
                )
            )

        metrics = self._build_metrics(
            initial_cash=request.initial_cash,
            ending_cash=cash,
            equity_curve=tuple(equity_curve),
            trade_count=len(simulated_trades),
        )
        return BacktestResult(
            backtest_id=backtest_id,
            symbol=series.symbol,
            market=series.market,
            timeframe=series.timeframe,
            time_range=time_range,
            source=series.source,
            simulated_trades=tuple(simulated_trades),
            equity_curve=tuple(equity_curve),
            metrics=metrics,
            final_position=position,
            signal_count=len(signals),
        )

    def _apply_signal(
        self,
        signal: ResearchSignal,
        bar: OHLCVBar,
        cash: float,
        position: SimulatedPosition,
        simulated_trades: list[SimulatedTrade],
        errors: list[BacktestValidationError],
    ) -> tuple[float, SimulatedPosition]:
        if signal.direction is BacktestDirection.HOLD:
            return cash, position

        if signal.direction is BacktestDirection.BUY and not position.is_open:
            if bar.close_price <= 0:
                errors.append(
                    BacktestValidationError(
                        message="Cannot simulate a BUY signal at a non-positive close_price.",
                        field_name="research_signals",
                        signal_timestamp=signal.timestamp,
                    )
                )
                return cash, position

            quantity = cash / bar.close_price
            if quantity <= 0:
                return cash, position

            simulated_trades.append(
                SimulatedTrade(
                    timestamp=bar.timestamp,
                    direction=BacktestDirection.BUY,
                    quantity=quantity,
                    price=bar.close_price,
                )
            )
            return 0.0, SimulatedPosition(
                quantity=quantity,
                average_entry_price=bar.close_price,
                opened_at=bar.timestamp,
            )

        if signal.direction is BacktestDirection.SELL and position.is_open:
            simulated_trades.append(
                SimulatedTrade(
                    timestamp=bar.timestamp,
                    direction=BacktestDirection.SELL,
                    quantity=position.quantity,
                    price=bar.close_price,
                )
            )
            return cash + (position.quantity * bar.close_price), SimulatedPosition()

        return cash, position

    def _build_metrics(
        self,
        *,
        initial_cash: float,
        ending_cash: float,
        equity_curve: tuple[EquityCurvePoint, ...],
        trade_count: int,
    ) -> BacktestMetrics:
        ending_equity = equity_curve[-1].equity
        total_return = (ending_equity - initial_cash) / initial_cash
        peak_equity = equity_curve[0].equity
        max_drawdown = 0.0

        for point in equity_curve:
            if point.equity > peak_equity:
                peak_equity = point.equity
                continue
            if peak_equity > 0:
                drawdown = (peak_equity - point.equity) / peak_equity
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return BacktestMetrics(
            initial_cash=initial_cash,
            ending_cash=ending_cash,
            ending_equity=ending_equity,
            total_return=total_return,
            max_drawdown=max_drawdown,
            trade_count=trade_count,
        )
