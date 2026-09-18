# -*- coding: utf-8 -*-
# ASCII-PURE: TIDAK ADA emoji literal di file ini. Semua emoji lewat \\U?????? escape
# sehingga runtime Python yang mengubahnya jadi karakter nyata (aman dari tool tulis).
# Modul: Budget Bulanan + Alert (per kategori, batas, alert 80% & 100%).
import io
import os
import json
import base64
from datetime import date, datetime

from telegram import Update
from telegram.ext import ContextTypes

from .handlers import _format_money, _period_transactions, calculate_period_summary, _now

# Lokasi simpan di luar source: <root>/data/budget.json
_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUDGET_DIR = os.path.join(_ROOT, "data")
BUDGET_FILE = os.path.join(BUDGET_DIR, "budget.json")


def _b64s(text: str) -> str:
    b = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return b


# ---------- persistensi ----------
def _load_budgets() -> dict:
    """Format: {"month:YYYY-MM": {"kategori": {"limit": int, "label": str}}}"""
    try:
        raw = io.open(BUDGET_FILE, encoding="utf-8").read()
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _save_budgets(data: dict) -> None:
    try:
        os.makedirs(BUDGET_DIR, exist_ok=True)
    except OSError:
        pass
    io.open(BUDGET_FILE, "w", encoding="utf-8", newline="").write(
        json.dumps(data, ensure_ascii=False, indent=2)
    )


def _month_key(d: date = None) -> str:
    d = d or _now().date()
    return d.strftime("%Y-%m")


def _is_target_month(d, start, end) -> bool:
    return start <= d <= end


# ---------- alert ----------
def _budget_alert(txs, start, end) -> str:
    """Sisipan footer /today /week /month: beri tahu kategori yang mondar-mandir
    melewati 80% atau 100% batas anggaran bulan berjalan."""
    month = _month_key()
    budgets = _load_budgets().get(month, {})
    if not budgets:
        return ""

    # total pengeluaran per kategori pada periode tsb
    spent = {}
    for tx in txs:
        if str(tx.type) == "expense":
            spent.setdefault(str(tx.category), 0)
            spent[str(tx.category)] += float(tx.amount or 0)

    warnings = []
    for cat, cfg in budgets.items():
        limit = float(cfg.get("limit") or 0)
        if limit <= 0 or cat not in spent:
            continue
        used = spent[cat]
        pct = used / limit * 100.0
        label = str(cfg.get("label") or cat)
        if pct >= 100.0:
            warnings.append(
                f"\U000026A0 *{label}* MELAMPAUI \u2014 {_format_money(used)} dari *{_format_money(limit)}* ({pct:.0f}%)"
            )
        elif pct >= 80.0:
            warnings.append(
                f"\U0001F6A9 *{label}* \u2248 \U0001F4B0 *{pct:.0f}%* terpakai ({_format_money(used)}/{_format_money(limit)})"
            )

    if not warnings:
        return ""
    return "\n\n" + "\n".join(warnings)


# ---------- command ----------
async def cmd_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = (context.args or [])
    arg = " ".join(args).strip()

    # /budget set <kategori> <nominal> | /budget <kategori> <nominal> | /budget hapus <kategori>
    words = arg.split()
    op = "lihat"
    cat = None
    val = None
    if words:
        first = words[0].lower()
        if first == "hapus":
            op = "hapus"
            cat = " ".join(words[1:]) or None
        elif first == "set" and len(words) >= 3:
            op = "set"
            cat = words[1]
            try:
                val = float(words[2].replace(".", "").replace(",", ""))
            except ValueError:
                val = None
        elif first in ("tambah", "edit", "guna") and len(words) >= 3:
            op = "set"
            cat = words[1]
            try:
                val = float(words[2].replace(".", "").replace(",", ""))
            except ValueError:
                val = None
        elif len(words) >= 2:
            # misal: makan 500000
            try:
                val = float(words[-1].replace(".", "").replace(",", ""))
                cat = " ".join(words[:-1])
                op = "set"
            except ValueError:
                op = "lihat"
        elif len(words) == 1:
            op = "lihat"

    month = _month_key()
    data = _load_budgets()
    bucket = data.setdefault(month, {})

    if op == "set":
        if cat is None or val is None or val <= 0:
            await update.message.reply_text(
                "Format /budget salah. Contoh:\n"
                "/budget set makan 500000\n"
                "/budget makan 500000"
            )
            return
        bucket[cat] = {"limit": int(val), "label": cat}
        _save_budgets(data)
        await update.message.reply_text(
            f"OK. Batas *{cat}* bulan ini: *{_format_money(int(val))}*"
        )
        return

    if op == "hapus":
        if cat is None:
            await update.message.reply_text("/budget hapus <kategori>")
            return
        if cat in bucket:
            del bucket[cat]
            if not bucket:
                data.pop(month, None)
            _save_budgets(data)
            await update.message.reply_text(f"Budget *{cat}* dihapus.")
        else:
            await update.message.reply_text(f"Budget *{cat}* tak ada.")
        return

    # lihat ------------------------------------------------------------------
    today = _now().date()
    start = today.replace(day=1)
    end = today
    txs = await _period_transactions(update, start, end)
    spent = {}
    for tx in txs:
        if str(tx.type) == "expense":
            spent.setdefault(str(tx.category), 0)
            spent[str(tx.category)] += float(tx.amount or 0)

    if not bucket:
        lines = ["\U0001F4CB Belum ada budget bulan ini."]
        lines.append("Gunakan: /budget set <kategori> <nominal>")
        await update.message.reply_text("\n".join(lines))
        return

    lines = [f"\U0001F4B0 *Budget {month}*"]
    for cat, cfg in bucket.items():
        limit = float(cfg.get("limit") or 0)
        used = spent.get(cat, 0)
        pct = (used / limit * 100.0) if limit > 0 else 0
        label = str(cfg.get("label") or cat)
        state = "\U00002705" if pct < 80 else ("\U0001F6A9" if pct < 100 else "\U000026A0")
        used_s = _format_money(int(used))
        lim_s = _format_money(int(limit))
        lines.append(
            f"{state} *{label}*: {used_s} / {lim_s}  ({pct:.0f}%)"
        )
    await update.message.reply_text("\n".join(lines))
