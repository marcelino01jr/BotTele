import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings
from app.schemas.schemas import ParsedTransaction

logger = logging.getLogger(__name__)

USER_IDENTIFICATION_SYSTEM_PROMPT = (
    "Kamu adalah asisten pencatat keuangan. Ubah input natural language pengguna "
    "menjadi data keuangan terstruktur. Keluarkan HANYA JSON valid tanpa teks lain.\n"
    "Skema JSON:\n"
    "{\n"
    '  "type": "income" | "expense" | "investment",\n'
    '  "amount": <angka desimal, contoh: 25000>,\n'
    '  "category": "<salah satu kategori>",\n'
    '  "subcategory": "<sub kategori atau null>",\n'
    '  "description": "<deskripsi singkat>",\n'
    '  "transaction_date": "<YYYY-MM-DD>"\n'
    "}\n"
    "Aturan:\n"
    "- 'makan', 'makanan', 'nasi', 'geprek' dll -> type=expense, category=Food.\n"
    "- 'gaji', 'upah', 'honor' -> type=income, category=Salary.\n"
    "- 'investasi', 'saham', 'reksadana', 'emas' -> type=investment, category=Investment.\n"
    "- 'ojek', 'grab', 'gojek', 'bensin' -> type=expense, category=Transport.\n"
    "- 'listrik', 'internet', 'wifi', 'pulsa', 'air' -> type=expense, category=Bills.\n"
    "- 'belanja', 'baju', 'sepatu' -> type=expense, category=Shopping.\n"
    "- 'nonton', 'film', 'konser', 'game' -> type=expense, category=Entertainment.\n"
    "- 'obat', 'dokter', 'klinik' -> type=expense, category=Health.\n"
    "- 'les', 'kuliah', 'buku' -> type=expense, category=Education.\n"
    "- 'kado', 'ultah' -> type=expense, category=Family.\n"
    "- 'kontrak', 'sewa rumah', 'kos' -> type=expense, category=Housing.\n"
    "- 'lainnya' atau tidak jelas -> category=Other.\n"
    "- Kategori yang tersedia: Food, Transport, Housing, Bills, Shopping, "
    "Entertainment, Health, Education, Family, Investment, Salary, Other.\n"
    "- 'transaction_date': hari ini di Asia/Jakarta jika tidak disebutkan. "
    "Jika pengguna menyebutkan 'kemarin', 'tadi malam', atau tanggal spesifik, "
    "gunakan tanggal yang disebutkan (format YYYY-MM-DD).\n"
    f"- Hari ini di Asia/Jakarta: {datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat()}.\n"
    "- amount harus angka positif tanpa simbol. '25 ribu' -> 25000, '1jt' -> 1000000, '2,5jt' -> 2500000.\n"
)


def _build_messages(user_text: str) -> list[dict]:
    return [
        {"role": "system", "content": USER_IDENTIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]


def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise


def _normalize_fields(data: dict, user_text: str) -> dict:
    data["type"] = str(data.get("type", "expense")).lower()
    data["category"] = str(data.get("category", "Other")).strip()

    if not data.get("description"):
        data["description"] = user_text

    if not data.get("transaction_date"):
        data["transaction_date"] = datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()

    return data


def parse_transaction_with_qwen(user_text: str, api_key: str | None = None) -> ParsedTransaction:
    settings = get_settings()
    api_key = api_key or settings.QWEN_API_KEY
    if not api_key:
        raise RuntimeError("QWEN_API_KEY tidak dikonfigurasi di .env")

    payload = {
        "model": settings.QWEN_MODEL,
        "messages": _build_messages(user_text),
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = httpx.post(
        f"{settings.QWEN_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = _parse_json_response(content)

    parsed = _normalize_fields(parsed, user_text)

    return ParsedTransaction(**parsed)