# -*- coding: utf-8 -*-
import io
import re
import sys

H = r"D:\New folder\BotTele\app\telegram\handlers.py"

with io.open(H, "r", encoding="utf-8") as f:
    src = f.read()

# --- 1) temukan blok cmd_start dari 'async def cmd_start' sampai
#        baris 'async def ' berikutnya (regardless of content) ---
m = re.search(r"^async def cmd_start\b.*?(?=^async def |\Z)", src, re.S | re.M)
if not m:
    print("NO_CMD_START")
    sys.exit(1)
block = m.group(0)

# --- 2) dalam block, hapus seluruh argumen panggilan reply_text ---
#        targetkan blok multi-baris sampai ')' penutup di akhir fungsi
rm = re.search(r"await update\.message\.reply_text\(\n(.*?)\n    \)", block, re.S)
if not rm:
    print("NO_REPLY_CALL")
    sys.exit(1)

print("=== ISI reply_text LAMA (dicetak sebagai repr, biar spasi/emoji pasti) ===")
print(repr(rm.group(1)))

new_args = (
    'f"Halo {first_name}! \U0001f44b\\n\\n"\n'
    '        "Aku *PunyaMarcelBot*, asisten keuangan pribadimu.\\n"\n'
    '        "Catat pemasukan dan pengeluaran cukup dengan mengetik:\\n"\n'
    '        "`makan ayam geprek 25 ribu`\\n\\n"\n'
    '        "Ketik /help untuk melihat semua perintah."'
)

# --- 3) ganti di block, lalu tempel kembali ke src ---
new_block = block[: rm.start(1)] + new_args + block[rm.end(1):]
src2 = src[: m.start(0)] + new_block + src[m.end(0):]

if src2 != src:
    with io.open(H, "w", encoding="utf-8", newline="") as f:
        f.write(src2)
    print("\nDITULIS: ", H)
else:
    print("\nTIDAK BERUBAH (paranoid check)")

# --- 4) verifikasi parse AST ---
import ast
try:
    ast.parse(src2)
    print("AST-valid: OK")
except SyntaxError as e:
    print("AST-valid: SYNTAX ERROR ->", e)
