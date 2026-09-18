import asyncio
import traceback

from app.ai.insight import generate_insight
from app.services.financial import weekly_comparison


SAMPLE = [
    {"type": "expense", "amount": "15000", "category": "Food",    "transaction_date": "2026-09-15"},
    {"type": "income",  "amount": "3000000", "category": "Salary", "transaction_date": "2026-09-14"},
    {"type": "expense", "amount": "50000", "category": "Transport","transaction_date": "2026-09-17"},
]


async def main() -> None:
    try:
        data = weekly_comparison([])
        print("weekly_comparison([]) -> OK:", list(data.keys()))
    except Exception:
        print("weekly_comparison FAIL:")
        traceback.print_exc()

    try:
        result = await asyncio.to_thread(generate_insight, SAMPLE)
        print("generate_insight OK ->", result)
    except Exception as e:
        print("generate_insight FAILED:")
        traceback.print_exc()


asyncio.run(main())
