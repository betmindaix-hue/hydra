from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hydra.domain.backtesting import BacktestId, BacktestTimeRange
from hydra.domain.market_data import DataSourceDescriptor, Market, Symbol, Timeframe
from hydra.domain.research_reporting import (
    EquityCurveSummary,
    MetricSnapshot,
    ResearchReport,
    ResearchReportId,
    RiskSnapshot,
    SignalSummary,
    SimulatedTradeSummary,
)


def make_time_range() -> BacktestTimeRange:
    return BacktestTimeRange(
        start=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        end=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
    )


def make_metric_snapshot() -> MetricSnapshot:
    return MetricSnapshot(
        initial_cash=1000,
        ending_cash=1100,
        ending_equity=1100,
        total_return=0.1,
        max_drawdown=0.05,
        trade_count=2,
        signal_count=3,
    )


def make_equity_curve_summary() -> EquityCurveSummary:
    return EquityCurveSummary(
        point_count=2,
        first_timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        last_timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
        starting_equity=1000,
        ending_equity=1100,
        min_equity=950,
        max_equity=1100,
        lowest_cash=0,
        highest_position_quantity=10,
    )


def make_signal_summary() -> SignalSummary:
    return SignalSummary(
        backtest_signal_count=2,
        research_signal_count=3,
        rejected_signal_count=1,
        research_error_count=1,
        buy_signal_count=1,
        sell_signal_count=1,
        hold_signal_count=1,
    )


def make_trade_summary() -> SimulatedTradeSummary:
    return SimulatedTradeSummary(
        trade_count=2,
        buy_count=1,
        sell_count=1,
        first_trade_timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
        last_trade_timestamp=datetime(2026, 7, 18, 10, 4, tzinfo=UTC),
    )


def make_risk_snapshot() -> RiskSnapshot:
    return RiskSnapshot(
        max_drawdown=0.05,
        total_return=0.1,
        final_position_open=False,
        final_position_quantity=0,
        final_position_average_entry_price=0,
    )


def make_report() -> ResearchReport:
    return ResearchReport(
        report_id=ResearchReportId("  report-1  "),
        title="  B6 Report  ",
        backtest_id=BacktestId(" backtest-1 "),
        symbol=Symbol("btcusdt"),
        market=Market("spot"),
        timeframe=Timeframe.MINUTE_1,
        time_range=make_time_range(),
        source=DataSourceDescriptor(name="report-series"),
        metrics=make_metric_snapshot(),
        equity_curve=make_equity_curve_summary(),
        signals=make_signal_summary(),
        simulated_trades=make_trade_summary(),
        risk=make_risk_snapshot(),
        notes=("  first note  ", " ", "second note"),
    )


def test_research_report_id_strips_value() -> None:
    report_id = ResearchReportId("  b6-report  ")

    assert report_id.value == "b6-report"
    assert str(report_id) == "b6-report"


def test_research_report_id_rejects_blank_and_non_string() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        ResearchReportId("   ")

    with pytest.raises(ValueError, match="must be a string"):
        ResearchReportId(1)  # type: ignore[arg-type]


def test_metric_snapshot_accepts_valid_values() -> None:
    snapshot = make_metric_snapshot()

    assert snapshot.initial_cash == 1000
    assert snapshot.signal_count == 3


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("initial_cash", 0, "initial_cash must be positive"),
        ("ending_cash", -1, "ending_cash must be non-negative"),
        ("ending_equity", -1, "ending_equity must be non-negative"),
        ("total_return", -1.5, "total_return cannot be less than -1"),
        ("max_drawdown", 1.5, "max_drawdown must stay between 0 and 1"),
        ("trade_count", -1, "trade_count must be non-negative"),
        ("signal_count", -1, "signal_count must be non-negative"),
    ),
)
def test_metric_snapshot_rejects_invalid_values(
    field_name: str,
    value: float | int,
    message: str,
) -> None:
    initial_cash = 1000.0
    ending_cash = 1100.0
    ending_equity = 1100.0
    total_return = 0.1
    max_drawdown = 0.05
    trade_count = 2
    signal_count = 3

    if field_name == "initial_cash":
        initial_cash = float(value)
    elif field_name == "ending_cash":
        ending_cash = float(value)
    elif field_name == "ending_equity":
        ending_equity = float(value)
    elif field_name == "total_return":
        total_return = float(value)
    elif field_name == "max_drawdown":
        max_drawdown = float(value)
    elif field_name == "trade_count":
        trade_count = int(value)
    else:
        signal_count = int(value)

    with pytest.raises(ValueError, match=message):
        MetricSnapshot(
            initial_cash=initial_cash,
            ending_cash=ending_cash,
            ending_equity=ending_equity,
            total_return=total_return,
            max_drawdown=max_drawdown,
            trade_count=trade_count,
            signal_count=signal_count,
        )


def test_equity_curve_summary_accepts_valid_values() -> None:
    summary = make_equity_curve_summary()

    assert summary.point_count == 2
    assert summary.ending_equity == 1100


def test_equity_curve_summary_rejects_zero_point_count() -> None:
    with pytest.raises(ValueError, match="point_count must be positive"):
        EquityCurveSummary(
            point_count=0,
            first_timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            last_timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
            starting_equity=1000,
            ending_equity=1100,
            min_equity=1000,
            max_equity=1100,
            lowest_cash=1000,
            highest_position_quantity=0,
        )


def test_equity_curve_summary_rejects_naive_timestamps() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        EquityCurveSummary(
            point_count=1,
            first_timestamp=datetime(2026, 7, 18, 10, 0),
            last_timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
            starting_equity=1000,
            ending_equity=1000,
            min_equity=1000,
            max_equity=1000,
            lowest_cash=1000,
            highest_position_quantity=0,
        )


def test_equity_curve_summary_rejects_invalid_min_max_equity() -> None:
    with pytest.raises(ValueError, match="min_equity cannot exceed max_equity"):
        EquityCurveSummary(
            point_count=1,
            first_timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            last_timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
            starting_equity=1000,
            ending_equity=1000,
            min_equity=1200,
            max_equity=1100,
            lowest_cash=1000,
            highest_position_quantity=0,
        )


def test_signal_summary_accepts_optional_none_counts() -> None:
    summary = SignalSummary(backtest_signal_count=2)

    assert summary.research_signal_count is None
    assert summary.hold_signal_count is None


def test_signal_summary_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        SignalSummary(
            backtest_signal_count=2,
            research_error_count=-1,
        )


def test_simulated_trade_summary_accepts_zero_trade_summary_with_none_timestamps() -> None:
    summary = SimulatedTradeSummary(
        trade_count=0,
        buy_count=0,
        sell_count=0,
    )

    assert summary.first_trade_timestamp is None
    assert summary.last_trade_timestamp is None


def test_simulated_trade_summary_accepts_positive_trade_summary() -> None:
    summary = make_trade_summary()

    assert summary.trade_count == 2
    assert summary.buy_count == 1
    assert summary.sell_count == 1


def test_simulated_trade_summary_rejects_count_mismatch() -> None:
    with pytest.raises(ValueError, match="must equal trade_count"):
        SimulatedTradeSummary(
            trade_count=2,
            buy_count=2,
            sell_count=1,
            first_trade_timestamp=datetime(2026, 7, 18, 10, 0, tzinfo=UTC),
            last_trade_timestamp=datetime(2026, 7, 18, 10, 5, tzinfo=UTC),
        )


def test_risk_snapshot_accepts_valid_values() -> None:
    snapshot = make_risk_snapshot()

    assert snapshot.final_position_open is False
    assert snapshot.final_position_quantity == 0


def test_risk_snapshot_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="max_drawdown must stay between 0 and 1"):
        RiskSnapshot(
            max_drawdown=1.5,
            total_return=0,
            final_position_open=False,
            final_position_quantity=0,
            final_position_average_entry_price=0,
        )

    with pytest.raises(ValueError, match="total_return cannot be less than -1"):
        RiskSnapshot(
            max_drawdown=0.1,
            total_return=-1.5,
            final_position_open=False,
            final_position_quantity=0,
            final_position_average_entry_price=0,
        )

    with pytest.raises(ValueError, match="final_position_quantity must be 0"):
        RiskSnapshot(
            max_drawdown=0.1,
            total_return=0,
            final_position_open=False,
            final_position_quantity=1,
            final_position_average_entry_price=100,
        )


def test_research_report_strips_title_and_notes() -> None:
    report = make_report()

    assert report.title == "B6 Report"
    assert report.notes == ("first note", "second note")


def test_research_report_removes_blank_notes() -> None:
    report = make_report()

    assert " " not in report.notes


def test_research_report_stores_notes_immutably() -> None:
    report = make_report()

    assert isinstance(report.notes, tuple)
    with pytest.raises(TypeError):
        report.notes[0] = "changed"  # type: ignore[index]
