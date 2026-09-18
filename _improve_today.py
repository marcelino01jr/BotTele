# -*- coding: utf-8 -*-
import io
import re
import sys

H = r"D:\New folder\BotTele\app\telegram\handlers.py"
RPT = r"D:\New folder\BotTele\_improve_report.txt"
report = []

src = io.open(H, encoding="utf-8").read()

# ---------- 1) _format_tx_line ----------
# label Indonesia + jumlah ditebalkan; icon jelas utk income/expense/invest
new_tx = (
    'def _format_tx_line(tx) -> str:\n'
    '    labels = {\n'
    '        "income": ("\u0001F4B0", "Pemasukan"),\n'
    '        "expense": ("\u0001F4B8", "Pengeluaran"),\n'
    '        "investment": ("\u0001F48E", "Investasi"),\n'
    '    }\n'
    '    icon, label = labels.get(str(tx.type), ("\u0001F4B0", "Transaksi"))\n'
    '    return (\n'
    '        f"{icon} *{label}* \\u2014 *{_format_money(tx.amount)}*\\n"\n'
    '        f"    {tx.category} \\u00b7 {tx.transaction_date}\\n"\n'
    '        f"    {tx.description}"\n'
    '    )'
)

m = re.search(
    r'^def _format_tx_line\b.*?(?=\n\s*def |\n\s*async def |\Z)',
    src, re.S | re.M,
)
if not m:
    report.append("ERR: _format_tx_line tidak ditemukan")
    io.open(RPT, "w", encoding="utf-8").write("\n".join(report))
    sys.exit(1)
old_tx = m.group(0)
if "_format_money(tx.amount)" in old_tx and "catatan" not in old_tx:
    src = src[: m.start()] + new_tx + src[m.end() :]
    report.append("OK: _format_tx_line diganti")
else:
    report.append("WARN: _format_tx_line bentuk lain -> dicek manual")
    report.append(repr(old_tx[:120]))

# ---------- 2) footer tiap cmd (today / week / month) ----------
footer_new = (
    '    footer = (\n'
    '        f"\\n\\n\U0001F4B8 *Total Pengeluaran:* {_format_money(summary.total_expense)}\\n"\n'
    '        f"\U0001F4B0 *Total Pemasukan:* {_format_money(summary.total_income)}\\n"\n'
    '        f"\U0001F48E *Total Investasi:* {_format_money(summary.total_investment)}"\n'
    '    )'
)

for fname in ("cmd_today", "cmd_week", "cmd_month"):
    mf = re.search(
        r'^async def ' + fname + r'\b.*?(?=\n\s*async def |\Z)',
        src, re.S | re.M,
    )
    if not mf:
        report.append("WARN: %s tidak ada" % fname)
        continue
    blk = mf.group(0)
    mf2 = re.search(
        r'footer = \(.*?\)(?=\n\s*await update\.message\.reply_text\(header)',
        blk, re.S,
    )
    if not mf2:
        report.append("WARN: footer tak ketemu di %s" % fname)
        continue
    newblk = blk[: mf2.start()] + footer_new + blk[mf2.end() :]
    src = src[: mf.start()] + newblk + src[mf.end() :]
    report.append("OK: footer %s diganti" % fname)

# ---------- tulis + verifikasi ----------
io.open(H, "w", encoding="utf-8", newline="").write(src)

import ast
try:
    ast.parse(src)
    report.append("SYNTAX_OK")
except SyntaxError as e:
    report.append("SYNTAX_ERR %r" % e)

io.open(RPT, "w", encoding="utf-8").write("\n".join(report))
print("SELESAI")
