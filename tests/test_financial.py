from datetime import date, datetime, timedelta
from decimal import Decimal

from app.services.financial import (
    build_weekly_report,
    calculate_period_summary,
    format_rupiah,
    weekly_comparison,
)
from app.models.tables import Transaction


def _tx(amount, tx_type="expense", category="Food", d=None):
    tx = Transaction()
    tx.amount = Decimal(amount)
    tx.type = tx_type
    tx.category = category
    tx.transaction_date = d or date.today()
    return tx


def test_period_summary_income_expense_investment():
    today = date(2026, 9, 16)
    txs = [
        _tx("10000000", "income", "Salary", today),
        _tx("25000", "expense", "Food", today),
        _tx("50000", "expense", "Transport", today),
        _tx("1000000", "investment", "Investment", today),
    ]

    summary = calculate_period_summary(txs, today, today)

    assert summary.total_income == Decimal("10000000")
    assert summary.total_expense == Decimal("75000")
    assert summary.total_investment == Decimal("1000000")
    assert summary.net_cash_flow == Decimal("10000000") - Decimal("75000") - Decimal("1000000")
    assert summary.transaction_count == 4


def test_period_summary_category_breakdown():
    today = date(2026, 9, 16)
    txs = [
        _tx("10000", "expense", "Food", today),
        _tx("20000", "expense", "Food", today),
        _tx("30000", "expense", "Transport", today),
    ]

    summary = calculate_period_summary(txs, today, today)

    by_name = {c.category: c for c in summary.category_breakdown}
    assert by_name["Food"].total == Decimal("30000")
    assert by_name["Food"].count == 2
    assert by_name["Transport"].total == Decimal("30000")
    assert summary.category_breakdown[0].total == Decimal("30000")


def test_period_summary_empty():
    today = date(2026, 9, 16)
    summary = calculate_period_summary([], today, today)
    assert summary.total_income == Decimal("0")
    assert summary.total_expense == Decimal("0")
    assert summary.net_cash_flow == Decimal("0")
    assert summary.transaction_count == 0
    assert summary.category_breakdown == []


def test_weekly_comparison_current_vs_previous():
    today = date(2026, 9, 16)
    previous_week = today - timedelta(days=8)
    current_week = today

    txs = [
        _tx("100000", "expense", "Food", current_week),
        _tx("50000", "expense", "Food", previous_week),
    ]

    result = weekly_comparison(txs, now=datetime(2026, 9, 16, 12, 0))

    current = result["current_week"]
    previous = result["previous_week"]
    assert current["total_expense"] == Decimal("100000")
    assert previous["total_expense"] == Decimal("50000")
    assert result["expense_change_pct"] == 100.0


def test_weekly_comparison_no_previous_week():
    today = date(2026, 9, 16)
    txs = [_tx("100000", "expense", "Food", today)]

    result = weekly_comparison(txs, now=datetime(2026, 9, 16, 12, 0))

    assert result["previous_week"]["total_expense"] == Decimal("0")
    assert result["expense_change_pct"] == 100.0


def test_weekly_comparison_previous_zero_current_zero():
    today = date(2026, 9, 16)
    result = weekly_comparison([], now=datetime(2026, 9, 16, 12, 0))
    assert result["expense_change_pct"] == 0.0


def test_build_weekly_report():
    today = date(2026, 9, 16)
    txs = [_tx("100000", "expense", "Food", today)]

    report = build_weekly_report(txs, now=datetime(2026, 9, 16, 12, 0))

    assert report.period_start == today - timedelta(days=6)
    assert report.period_end == today
    assert report.total_expense == Decimal("100000")
    assert report.top_categories[0]["category"] == "Food"
    assert report.net_cash_flow == Decimal("-100000")


def test_format_rupiah():
    assert format_rupiah(Decimal("25000")) == "Rp 25.000"
    assert format_rupiah(Decimal("1000000")) == "Rp 1.000.000"
    assert format_rupiah("5000000") == "Rp 5.000.000"