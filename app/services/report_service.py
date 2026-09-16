from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.ai.insight import generate_insight
from app.models.tables import User
from app.schemas.schemas import WeeklyReport
from app.services.financial import build_weekly_report
from app.services.transaction_service import list_transactions
from sqlalchemy.orm import Session


def get_weekly_report(db: Session, user: User) -> WeeklyReport:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    transactions = list_transactions(
        db,
        user,
        start_date=now.date() - timedelta(days=6),
        end_date=now.date(),
    )
    return build_weekly_report(transactions, now=now)


def format_weekly_report(report: WeeklyReport) -> str:
    lines = [
        "🗓️ *Laporan Mingguan*",
        f"Periode: {report.period_start} s/d {report.period_end}",
        "",
        f"💰 *Pemasukan:* Rp {report.total_income:,.0f}",
        f"💸 *Pengeluaran:* Rp {report.total_expense:,.0f}",
        f"📈 *Investasi:* Rp {report.total_investment:,.0f}",
        f"📊 *Net Cash Flow:* Rp {report.net_cash_flow:,.0f}",
    ]
    if report.top_categories:
        lines.extend(["", "*Top Kategori:*"])
        for cat in report.top_categories:
            lines.append(
                f"• {cat['category']}: Rp {cat['total']:,.0f} "
                f"({cat['count']}x)"
            )
    return "\n".join(lines)


def get_weekly_report_with_insights(db: Session, user: User) -> WeeklyReport:
    report = get_weekly_report(db, user)
    transactions = list_transactions(
        db,
        user,
        start_date=report.period_start - timedelta(days=7),
        end_date=report.period_end,
    )
    from app.services.financial import weekly_comparison

    comparison = weekly_comparison(transactions, now=datetime.now(ZoneInfo("Asia/Jakarta")))
    insight = generate_insight(comparison)
    report.insights = insight.highlights + insight.recommendations
    return report