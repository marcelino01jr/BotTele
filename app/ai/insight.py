import json
import logging

import httpx

from app.ai.parser import _parse_json_response
from app.config import get_settings
from app.schemas.schemas import InsightResult
from app.services.financial import weekly_comparison

logger = logging.getLogger(__name__)

INSIGHT_SYSTEM_PROMPT = (
    "Kamu adalah analis keuangan pribadi. Analisis data perbandingan pengeluaran "
    "minggu berjalan (7 hari terakhir) versus minggu sebelumnya.\n"
    "Keluarkan HANYA JSON valid dengan skema berikut, tanpa teks lain:\n"
    "{\n"
    '  "summary": "<ringkasan 2-3 kalimat>",\n'
    '  "highlights": ["<temuan penting>", ...],\n'
    '  "recommendations": ["<saran aksi>", ...]\n'
    "}\n"
    "Gunakan bahasa Indonesia yang natural. Jangan menyebutkan angka yang salah "
    "atau membuat klaim yang tidak didukung data.\n"
)


def generate_insight(comparison_data: dict, api_key: str | None = None) -> InsightResult:
    settings = get_settings()
    api_key = api_key or settings.QWEN_API_KEY
    if not api_key:
        raise RuntimeError("QWEN_API_KEY tidak dikonfigurasi di .env")

    payload = {
        "model": settings.QWEN_MODEL,
        "messages": [
            {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(comparison_data, ensure_ascii=False, default=str)},
        ],
        "temperature": 0.3,
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

    return InsightResult(**parsed)


def build_insight_input(transactions) -> dict:
    return weekly_comparison(transactions)