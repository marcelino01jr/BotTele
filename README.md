# PunyaMarcelBot 🤖

AI personal finance assistant berbasis Telegram.

Kirim transaksi dengan bahasa natural (mis. `makan ayam geprek 25 ribu`), AI (Qwen) mengubahnya jadi data terstruktur, lalu disimpan di PostgreSQL (Neon). Semua perhitungan finansial dilakukan Python, bukan LLM.

## Fitur MVP

- Input natural language ke Telegram → Qwen → JSON terstruktur → Pydantic validation → simpan ke PostgreSQL.
- Komando: `/start`, `/help`, `/today`, `/week`, `/month`, `/summary`, `/insight`.
- `/summary`: income, expense, investment, net cash flow + breakdown kategori.
- `/insight`: analisis pola 7 hari terakhir vs minggu sebelumnya memakai Qwen.
- Kategori: Food, Transport, Housing, Bills, Shopping, Entertainment, Health, Education, Family, Investment, Salary, Other.
- Money memakai `Decimal`/`Numeric`, bukan float.
- Timezone `Asia/Jakarta` di semua perhitungan.
- Setiap user hanya bisa mengakses transaksinya sendiri.

## Struktur

```text
app/
├── main.py              # entry point
├── config.py            # pydantic-settings (load .env)
├── database/            # engine + session
├── models/              # SQLAlchemy models + enums kategori
├── schemas/             # Pydantic schemas (validation)
├── services/            # perhitungan finansial, transaksi, laporan
├── ai/                  # Qwen parser + insight generator
└── telegram/            # bot handlers
tests/                   # unit tests (pytest)
alembic/                 # database migration
.env.example
requirements.txt
```

## Setup

1. Install dependencies:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Salin `.env.example` menjadi `.env` lalu isi:

   ```
   TELEGRAM_BOT_TOKEN=<token dari @BotFather>
   DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname   # Neon
   QWEN_API_KEY=<dashscope API key>
   QWEN_MODEL=qwen-plus
   TIMEZONE=Asia/Jakarta
   ```

3. Jalankan migrasi database:

   ```bash
   alembic upgrade head
   ```

4. Jalankan bot:

   ```bash
   python -m app.main
   ```

## Test

```bash
pytest tests -v
```

## Cara pakai

Di chat Telegram dengan bot:

- `makan ayam geprek 25 ribu` → expense Food 25.000
- `gaji 10jt` → income Salary 10.000.000
- `investasi 1jt` → investment Investment 1.000.000
- `bensin kemarin 50rb` → expense Transport kemarin
- `/summary` → rekap bulan ini
- `/insight` → analisis AI pola pengeluaran

## Weekly report (scheduler)

Fungsi `get_weekly_report_with_insights` di `app/services/report_service.py` siap dipanggil scheduler/APScheduler untuk laporan otomatis mingguan.

## LLM provider

Default memakai Qwen (DashScope, OpenAI-compatible). `QWEN_BASE_URL`, `QWEN_MODEL`, `QWEN_API_KEY` bisa diganti dari `.env` untuk provider lain.