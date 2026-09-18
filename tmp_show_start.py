# -*- coding: utf-8 -*-
import io
import re
import sys

P = r"D:\New folder\BotTele\app\telegram\handlers.py"

with io.open(P, "r", encoding="utf-8") as f:
    src = f.read()

# Temukan body cmd_start
m = re.search(r"async def cmd_start.*?\n(    await update\.message\.reply_text\(.*?\)\n)", src, re.S)
if not m:
    print("TIDAK ADA blok reply_text di cmd_start")
    sys.exit(1)

block = m.group(1)
print("=== BLOCK LAMA (ditemukan otomatis) ===")
print(block)
