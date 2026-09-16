from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.enums import Category, TransactionType
from app.schemas.schemas import CategorySummary, PeriodSummary, WeeklyReport
from app.models.tables import Transaction


def _as_decimal(value: Decimal | int | str | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(value)


def calculate_period_summary(
    transactions: list[Transaction],
    start_date: date,
    end_date: date,
) -> PeriodSummary:
    total_income = Decimal("0")
    total_expense = Decimal("0")
    total_investment = Decimal("0")
    category_totals: defaultdict[str, Decimal] = defaultdict(Decimal)
    category_counts: defaultdict[str, int] = defaultdict(int)

    for tx in transactions:
        amount = _as_decimal(tx.amount)
        tx_type = TransactionType(tx.type) if not isinstance(tx.type, TransactionType) else tx.type
        if tx_type == TransactionType.INCOME:
            total_income += amount
        elif tx_type == TransactionType.EXPENSE:
            total_expense += amount
        elif tx_type == TransactionType.INVESTMENT:
            total_investment += amount
        category_totals[str(tx.category)] += amount
        category_counts[str(tx.category)] += 1

    category_breakdown = [
        CategorySummary(
            category=Category(name),
            total=Decimal(category_totals[name]),
            count=category_counts[name],
        )
        for name in category_totals
    ]
    category_breakdown.sort(key=lambda c: c.total, reverse=True)

    return PeriodSummary(
        start_date=start_date,
        end_date=end_date,
        total_income=total_income,
        total_expense=total_expense,
        total_investment=total_investment,
        net_cash_flow=total_income - total_expense - total_investment,
        category_breakdown=category_breakdown,
        transaction_count=len(transactions),
    )


def weekly_comparison(
    transactions: list[Transaction],
    now: datetime | None = None,
) -> dict:
    """Compare the last 7 days against the previous 7 days.

    The current week is [today-6, today];
    the previous week is [today-13, today-7].
    """
    today = (now or datetime.now()).date()

    current_start = today - timedelta(days=6)
    previous_end = today - timedelta(days=7)
    previous_start = today - timedelta(days=13)

    current_txs = [
        tx for tx in transactions
        if current_start <= tx.transaction_date <= today
    ]
    previous_txs = [
        tx for tx in transactions
        if previous_start <= tx.transaction_date <= previous_end
    ]

    current = calculate_period_summary(current_txs, current_start, today)
    previous = calculate_period_summary(previous_txs, previous_start, previous_end)

    def pct_change(cur: Decimal, prev: Decimal) -> float:
        prev = _as_decimal(prev)
        if prev == 0:
            if cur > 0:
                return 100.0
            return 0.0
        return float(((cur - prev) / prev) * Decimal("100"))

    return {
        "current_week": {
            "start_date": current.start_date,
            "end_date": current.end_date,
            "total_expense": current.total_expense,
            "total_income": current.total_income,
            "total_investment": current.total_investment,
            "net_cash_flow": current.net_cash_flow,
        },
        "previous_week": {
            "start_date": previous.start_date,
            "end_date": previous.end_date,
            "total_expense": previous.total_expense,
            "total_income": previous.total_income,
            "total_investment": previous.total_investment,
            "net_cash_flow": previous.net_cash_flow,
        },
        "expense_change_pct": round(pct_change(current.total_expense, previous.total_expense), 2),
        "income_change_pct": round(pct_change(current.total_income, previous.total_income), 2),
        "investment_change_pct": round(pct_change(current.total_investment, previous.total_investment), 2),
        "top_expense_categories_current": [
            {"category": c.category, "total": str(c.total), "count": c.count}
            for c in current.category_breakdown
            if c.category in {
                Category.FOOD, Category.TRANSPORT, Category.HOUSING, Category.BILLS,
                Category.SHOPPING, Category.ENTERTAINMENT, Category.HEALTH,
                Category.EDUCATION, Category.FAMILY, Category.OTHER,
            }
        ][:5],
    }


def build_weekly_report(
    transactions: list[Transaction],
    now: datetime | None = None,
) -> WeeklyReport:
    today = (now or datetime.now()).date()
    start = today - timedelta(days=6)
    end = today

    summary = calculate_period_summary(transactions, start, end)

    return WeeklyReport(
        period_start=start,
        period_end=end,
        total_income=summary.total_income,
        total_expense=summary.total_expense,
        total_investment=summary.total_investment,
        net_cash_flow=summary.net_cash_flow,
        top_categories=[
            {"category": c.category, "total": c.total, "count": c.count}
            for c in summary.category_breakdown[:5]
        ],
    )


def format_rupiah(value: Decimal | int | float | str) -> str:
    dec = _as_decimal(value)
    return f"Rp {dec:,.0f}".replace(",", ".")