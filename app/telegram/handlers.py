import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from app.ai.insight import generate_insight
from app.ai.parser import parse_transaction_with_qwen
from app.database.session import SessionLocal
from app.services.financial import (
    calculate_period_summary,
    weekly_comparison,
)
from app.services.transaction_service import (
    create_transaction,
    list_transactions,
)
from app.services.user_service import get_or_create_user

logger = logging.getLogger(__name__)

TZ = ZoneInfo("Asia/Jakarta")

HELP_TEXT = (
    "📖 *PunyaMarcelBot - Bantuan*\n\n"
    "Cara pakai: ketik transaksi dengan bahasa natural.\n\n"
    "Contoh:\n"
    "• `makan ayam geprek 25 ribu`\n"
    "• `gaji 10jt`\n"
    "• `investasi 1jt`\n"
    "• `bensin kemarin 50rb`\n\n"
    "*Perintah:*\n"
    "/today - transaksi hari ini\n"
    "/week - transaksi 7 hari terakhir\n"
    "/month - transaksi bulan ini\n"
    "/summary - ringkasan bulan ini\n"
    "/insight - analisis AI pengeluaran\n"
    "/help - bantuan ini"
)


def _now() -> datetime:
    return datetime.now(TZ)


def _format_money(value) -> str:
    return f"Rp {value:,.0f}"


def _format_tx_line(tx) -> str:
    icon = {"income": "💰", "expense": "💸", "investment": "📈"}.get(str(tx.type), "•")
    return (
        f"{icon} *{str(tx.type).capitalize()}* — {_format_money(tx.amount)}\n"
        f"   {tx.category} · {tx.transaction_date}\n"
        f"   {tx.description}"
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    telegram_id = user.id
    first_name = user.first_name
    username = user.username

    with SessionLocal() as db:
        get_or_create_user(db, telegram_id, first_name, username)

    await update.message.reply_text(
        f"Halo {first_name}! 👋\n\n"
        "Aku *PunyaMarcelBot*, asisten keuangan pribadimu.\n"
        "Catat transaksi cukup dengan mengetik, contoh:\n"
        "`makan ayam geprek 25 ribu`\n\n"
        "Ketik /help untuk melihat semua perintah."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (update.message.text or "").strip()
    if not text:
        return

    with SessionLocal() as db:
        db_user = get_or_create_user(db, user.id, user.first_name, user.username)
        try:
            parsed = await asyncio.to_thread(parse_transaction_with_qwen, text)
        except Exception as exc:
            logger.exception("AI parse failed")
            await update.message.reply_text(
                "⚠️ Maaf, saya gagal memahami transaksimu. "
                "Coba lagi dengan format seperti: `makan 25rb`"
            )
            return

        try:
            tx = create_transaction(db, db_user, parsed)
        except Exception as exc:
            logger.exception("Failed to save transaction")
            await update.message.reply_text("⚠️ Gagal menyimpan transaksi. Coba lagi.")
            return

    amount_str = _format_money(tx.amount)
    await update.message.reply_text(
        "✅ Transaksi tersimpan!\n\n"
        f"📝 *{tx.description}*\n"
        f"• Tipe: {str(tx.type).capitalize()}\n"
        f"• Kategori: {tx.category}\n"
        f"• Subkategori: {tx.subcategory or '-'}\n"
        f"• Jumlah: {amount_str}\n"
        f"• Tanggal: {tx.transaction_date}"
    )


async def _period_transactions(update: Update, start: date, end: date) -> list:
    user = update.effective_user
    with SessionLocal() as db:
        db_user = get_or_create_user(db, user.id)
        return list_transactions(db, db_user, start_date=start, end_date=end)


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = _now().date()
    txs = await _period_transactions(update, today, today)
    if not txs:
        await update.message.reply_text("📭 Tidak ada transaksi hari ini.")
        return

    summary = calculate_period_summary(txs, today, today)
    header = f"📅 *Transaksi Hari Ini* ({today})\n\n"
    lines = [_format_tx_line(tx) for tx in txs]
    footer = (
        f"\n💵 Total: {_format_money(summary.total_expense)}\n"
        f"💰 Total In: {_format_money(summary.total_income)}\n"
        f"📈 Invest: {_format_money(summary.total_investment)}"
    )
    await update.message.reply_text(header + "\n".join(lines) + footer)


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    end = _now().date()
    start = end - timedelta(days=6)
    txs = await _period_transactions(update, start, end)
    if not txs:
        await update.message.reply_text("📭 Tidak ada transaksi 7 hari terakhir.")
        return

    summary = calculate_period_summary(txs, start, end)
    header = f"📅 *Transaksi 7 Hari Terakhir* ({start} s/d {end})\n\n"
    lines = [_format_tx_line(tx) for tx in txs]
    footer = (
        f"\n💵 Total: {_format_money(summary.total_expense)} · "
        f"💰 Total In: {_format_money(summary.total_income)} · "
        f"📈 Invest: {_format_money(summary.total_investment)}"
    )
    await update.message.reply_text(header + "\n".join(lines) + footer)


async def cmd_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = _now().date()
    start = today.replace(day=1)
    txs = await _period_transactions(update, start, today)
    if not txs:
        await update.message.reply_text("📭 Tidak ada transaksi bulan ini.")
        return

    summary = calculate_period_summary(txs, start, today)
    header = f"📅 *Transaksi Bulan Ini* ({start.strftime('%B %Y')})\n\n"
    lines = [_format_tx_line(tx) for tx in txs]
    footer = (
        f"\n💵 Total: {_format_money(summary.total_expense)} · "
        f"💰 Total In: {_format_money(summary.total_income)} · "
        f"📈 Invest: {_format_money(summary.total_investment)}"
    )
    await update.message.reply_text(header + "\n".join(lines) + footer)


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = _now().date()
    start = today.replace(day=1)
    user = update.effective_user

    with SessionLocal() as db:
        db_user = get_or_create_user(db, user.id)
        txs = list_transactions(db, db_user, start_date=start, end_date=today)

    if not txs:
        await update.message.reply_text("📭 Belum ada transaksi bulan ini.")
        return

    summary = calculate_period_summary(txs, start, today)

    lines = [
        "🧮 *Ringkasan Bulan Ini*",
        f"Periode: {start} s/d {today}",
        "",
        f"💰 *Pemasukan:* {_format_money(summary.total_income)}",
        f"💸 *Pengeluaran:* {_format_money(summary.total_expense)}",
        f"📈 *Investasi:* {_format_money(summary.total_investment)}",
        f"📊 *Net Cash Flow:* {_format_money(summary.net_cash_flow)}",
        "",
        "*Breakdown Kategori:*",
    ]

    if summary.category_breakdown:
        for cat in summary.category_breakdown:
            lines.append(f"• {cat.category}: {_format_money(cat.total)} ({cat.count}x)")
    else:
        lines.append("• Tidak ada data")

    lines.append("")
    lines.append(f"Jumlah transaksi: {summary.transaction_count}")

    await update.message.reply_text("\n".join(lines))


async def cmd_insight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    with SessionLocal() as db:
        db_user = get_or_create_user(db, user.id)
        txs = list_transactions(db, db_user)

    if not txs:
        await update.message.reply_text("📭 Belum ada data untuk dianalisis.")
        return

    comparison = weekly_comparison(txs, now=_now())

    await update.message.reply_text(
        "🔍 AI sedang menganalisis pola pengeluaranmu… (bisa beberapa detik)"
    )

    try:
        insight = await asyncio.to_thread(generate_insight, comparison)
    except Exception as exc:
        logger.exception("Insight generation failed")
        await update.message.reply_text(
            "⚠️ Gagal menghasilkan insight. "
            "Pastikan QWEN_API_KEY sudah diisi, atau coba lagi nanti."
        )
        return

    current = comparison["current_week"]
    previous = comparison["previous_week"]

    lines = [
        "📊 *Insight Mingguan*",
        "",
        f"Minggu ini ({current['start_date']} s/d {current['end_date']}):",
        f"• Pengeluaran: {_format_money(current['total_expense'])}",
        f"• Pemasukan: {_format_money(current['total_income'])}",
        f"• Investasi: {_format_money(current['total_investment'])}",
        "",
        f"Minggu lalu ({previous['start_date']} s/d {previous['end_date']}):",
        f"• Pengeluaran: {_format_money(previous['total_expense'])}",
        "",
        f"📉 Perubahan pengeluaran: {comparison['expense_change_pct']:+.1f}%",
        "",
        "*💡 Analisis AI:*",
        insight.summary,
    ]

    if insight.highlights:
        lines.append("\n*Highlight:*")
        for h in insight.highlights:
            lines.append(f"• {h}")

    if insight.recommendations:
        lines.append("\n*Rekomendasi:*")
        for r in insight.recommendations:
            lines.append(f"• {r}")

    await update.message.reply_text("\n".join(lines))