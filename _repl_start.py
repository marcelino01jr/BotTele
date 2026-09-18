# -*- coding: utf-8 -*-
import io
import re
import sys
import traceback

H = r"D:\New folder\BotTele\app\telegram\handlers.py"

try:
    with io.open(H, "r", encoding="utf-8") as f:
        src = f.read()
except Exception:
    traceback.print_exc()
    sys.exit(1)


def find_func(source: str, name: str):
    m = re.search(r"^async def " + name + r"\b.*?(?=^async def |\Z)", source, re.S | re.M)
    return m


fm = find_func(src, "cmd_start")
if not fm:
    print("FAIL: cmd_start tidak ditemukan")
    sys.exit(1)

blk = fm.group(0)
rm = re.search(
    r"await update\.message\.reply_text\("
    r".*?"
    r"\)",
    blk,
    re.S,
)
if not rm:
    print("FAIL: reply_text di cmd_start tidak ditemukan")
    sys.exit(1)

old_args = blk[rm.start(0) : rm.end(0)]

print("=== ISI PERSIS reply_text DI cmd_start (repr) ===")
print(repr(old_args))
print()

NEW_ARG = (
    "await update.message.reply_text(\n"
    '        f"Halo {first_name}! " \uD83D\uDC4B "\n\n"\n'
    '        "Aku `PunyaMarcelBot`, asisten keuangan pribadimu.\n"\n'
    '        "Catat pemasukan dan pengeluaranmu cukup dengan mengetik,\n"\n'
    '        "misalnya: `makan ayam geprek 25 ribu`.\n\n"\n'
    '        "Ketik /help untuk melihat semua perintah."\n'
    "    )"
)

blk2 = blk[: rm.start(0)] + NEW_ARG + blk[rm.end(0) :]
src2 = src[: fm.start(0)] + blk2 + src[fm.end(0) :]

if src2 == src:
    print("NO CHANGE")
    sys.exit(0)

with io.open(H, "w", encoding="utf-8", newline="") as f:
    f.write(src2)

print("DITULIS. Verifikasi -> ")
lines = src2.splitlines()
for i in range(66, 77):
    if i <= len(lines):
        print(i, repr(lines[i - 1]))
