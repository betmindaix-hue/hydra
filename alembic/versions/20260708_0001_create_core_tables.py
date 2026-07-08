"""create core research tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260708_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", "version", name="uq_experiments_name_version"),
    )
    op.create_index("ix_experiments_name", "experiments", ["name"])

    op.create_table(
        "market_bars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=False),
        sa.Column("high_price", sa.Float(), nullable=False),
        sa.Column("low_price", sa.Float(), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "symbol",
            "timeframe",
            "open_time",
            name="uq_market_bars_symbol_timeframe_open_time",
        ),
    )
    op.create_index("ix_market_bars_symbol", "market_bars", ["symbol"])
    op.create_index("ix_market_bars_timeframe", "market_bars", ["timeframe"])
    op.create_index("ix_market_bars_open_time", "market_bars", ["open_time"])

    op.create_table(
        "patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_patterns_name", "patterns", ["name"], unique=True)

    op.create_table(
        "performance_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=False),
        sa.Column("drawdown", sa.Float(), nullable=False),
        sa.Column("win_rate", sa.Float(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_performance_snapshots_as_of", "performance_snapshots", ["as_of"])

    op.create_table(
        "feature_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("market_bar_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_namespace", sa.String(length=64), nullable=False),
        sa.Column("feature_version", sa.String(length=32), nullable=False),
        sa.Column("values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_bar_id"], ["market_bars.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "market_bar_id",
            "feature_namespace",
            "feature_version",
            name="uq_feature_sets_market_bar_id",
        ),
    )
    op.create_index("ix_feature_sets_market_bar_id", "feature_sets", ["market_bar_id"])

    op.create_table(
        "strategy_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("feature_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_name", sa.String(length=64), nullable=False),
        sa.Column("strategy_version", sa.String(length=32), nullable=False),
        sa.Column("signal", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["feature_set_id"], ["feature_sets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_strategy_signals_feature_set_id", "strategy_signals", ["feature_set_id"])
    op.create_index("ix_strategy_signals_strategy_name", "strategy_signals", ["strategy_name"])

    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("strategy_signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("size_fraction", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_signal_id"], ["strategy_signals.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_decisions_strategy_signal_id", "decisions", ["strategy_signal_id"])

    op.create_table(
        "paper_trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_paper_trades_decision_id", "paper_trades", ["decision_id"])
    op.create_index("ix_paper_trades_symbol", "paper_trades", ["symbol"])
    op.create_index("ix_paper_trades_status", "paper_trades", ["status"])


def downgrade() -> None:
    op.drop_index("ix_paper_trades_status", table_name="paper_trades")
    op.drop_index("ix_paper_trades_symbol", table_name="paper_trades")
    op.drop_index("ix_paper_trades_decision_id", table_name="paper_trades")
    op.drop_table("paper_trades")

    op.drop_index("ix_decisions_strategy_signal_id", table_name="decisions")
    op.drop_table("decisions")

    op.drop_index("ix_strategy_signals_strategy_name", table_name="strategy_signals")
    op.drop_index("ix_strategy_signals_feature_set_id", table_name="strategy_signals")
    op.drop_table("strategy_signals")

    op.drop_index("ix_feature_sets_market_bar_id", table_name="feature_sets")
    op.drop_table("feature_sets")

    op.drop_index("ix_performance_snapshots_as_of", table_name="performance_snapshots")
    op.drop_table("performance_snapshots")

    op.drop_index("ix_patterns_name", table_name="patterns")
    op.drop_table("patterns")

    op.drop_index("ix_market_bars_open_time", table_name="market_bars")
    op.drop_index("ix_market_bars_timeframe", table_name="market_bars")
    op.drop_index("ix_market_bars_symbol", table_name="market_bars")
    op.drop_table("market_bars")

    op.drop_index("ix_experiments_name", table_name="experiments")
    op.drop_table("experiments")
