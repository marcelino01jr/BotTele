from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.tables import Transaction
from app.services.financial import weekly_comparison


def _tx(d, amount, tx_type="expense", category="Food"):
    tx = Transaction()
    tx.transaction_date = d
    tx.amount = Decimal(amount)
    tx.type = tx_type
    tx.category = category
    return tx


def test_comparison_boundaries():
    today = date(2026, 9, 16)
    now = datetime(2026, 9, 16, 0, 0)

    txs = [
        _tx(today - timedelta(days=13), "100", category="Bills"),
        _tx(today - timedelta(days=7), "200", category="Bills"),
        _tx(today - timedelta(days=6), "300", category="Food"),
        _tx(today, "400", category="Food"),
    ]

    result = weekly_comparison(txs, now=now)

    # previous week: day-13 and day-7 => 300
    assert result["previous_week"]["total_expense"] == Decimal("300")
    # current week: day-6 and day 0 => 700
    assert result["current_week"]["total_expense"] == Decimal("700")
    assert result["expense_change_pct"] == round((700 - 300) / 300 * 100, 2)


def test_comparison_income_category_breakdown():
    today = date(2026, 9, 16)
    now = datetime(2026, 9, 16, 0, 0)

    txs = [
        _tx(today, "1000000", "income", "Salary"),
        _tx(today, "50000", "expense", "Food"),
        _tx(today, "10000", "expense", "Transport"),
    ]

    result = weekly_comparison(txs, now=now)

    current = result["current_week"]
    assert current["total_income"] == Decimal("1000000")
    assert current["total_expense"] == Decimal("60000")
    assert current["net_cash_flow"] == Decimal("940000")

    top = result["top_expense_categories_current"]
    assert top[0]["category"] == "Food"
    assert top[0]["total"] == "50000"


def test_comparison_includes_investment():
    today = date(2026, 9, 16)
    now = datetime(2026, 9, 16, 0, 0)

    txs = [_tx(today, "1000000", "investment", "Investment")]

    result = weekly_comparison(txs, now=now)
    assert result["current_week"]["total_investment"] == Decimal("1000000")
    assert result["current_week"]["net_cash_flow"] == Decimal("-1000000")