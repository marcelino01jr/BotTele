# -*- coding: utf-8 -*-
import io
import re
import sys

H = r"D:\New folder\BotTele\app\telegram\handlers.py"

OLD = (
    'async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n'
    '    user = update.effective_user\n'
    '    first_name = user.first_name\n'
    '    username = user.username\n'
    '    telegram_id = user.id\n'
    '\n'
    '    with SessionLocal() as db:\n'
    '        get_or_create_user(db, telegram_id, first_name, username)\n'
    '\n'
    '    await update.message.reply_text(\n'
    '        f"Halo {first_name}! \U0001f44b\n\n"\n'
    '        "Aku *PunyaMarcelBot*, asisten keuangan pribadimu.\n"\n'
    '        "Catat transaksi cukup dengan mengetik, contoh:\n"\n'
    '        "`makan ayam geprek 25 ribu`\n\n"\n'
    '        "Ketik /help untuk melihat semua perintah."\n'
    '    )'
)

NEW = (
    'async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n'
    '    user = update.effective_user\n'
    '    first_name = user.first_name\n'
    '    username = user.username\n'
    '    telegram_id = user.id\n'
    '\n'
    '    with SessionLocal() as db:\n'
    '        get_or_create_user(db, telegram_id, first_name, username)\n'
    '\n'
    '    await update.message.reply_text(\n'
    '        f"Halo {first_name}! Halo!\n\n"\n'
    '        "Aku *PunyaMarcelBot*, asisten keuangan pribadimu.\n"\n'
    '        "Catat transaksi cukup dengan mengetik.\n\n"\n'
    '        "Ketik /help untuk melihat semua perintah."\n'
    '    )'
)

with io.open(H, "r", encoding="utf-8", newline="") as f:
    src = f.read()

if OLD not in src:
    print("OLD GAGAL COCOK. Mencari potongan...")
    for probe in ("async def cmd_start", "Halo {first_name}!", "contoh:"):
        i = src.find(probe)
        print("probe:", repr(probe), "->", i)
        if i >= 0:
            print("  ctx:", repr(src[i:i + 300]))
    sys.exit(1)

src = src.replace(OLD, NEW, 1)

with io.open(H, "w", encoding="utf-8", newline="") as f:
    f.write(src)

print("OK: cmd_start suddah dirapikan (contoh dihapus, ASCII-safe)")
