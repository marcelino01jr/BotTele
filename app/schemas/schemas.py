from datetime import date, datetime

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Category, TransactionType


class ParsedTransaction(BaseModel):
    type: TransactionType
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    category: Category
    subcategory: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    transaction_date: date = Field(default_factory=date.today)

    @field_validator("amount")
    @classmethod
    def amount_greater_than_zero(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be greater than zero")
        return v

    @field_validator("subcategory")
    @classmethod
    def strip_subcategory(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    model_config = ConfigDict(use_enum_values=True)


class InsightResult(BaseModel):
    summary: str
    highlights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class WeeklyReport(BaseModel):
    period_start: date
    period_end: date
    total_income: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    total_investment: Decimal = Decimal("0")
    net_cash_flow: Decimal = Decimal("0")
    top_categories: list[dict] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)


class CategorySummary(BaseModel):
    category: Category
    total: Decimal = Decimal("0")
    count: int = 0

    model_config = ConfigDict(use_enum_values=True)


class PeriodSummary(BaseModel):
    start_date: date
    end_date: date
    total_income: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    total_investment: Decimal = Decimal("0")
    net_cash_flow: Decimal = Decimal("0")
    category_breakdown: list[CategorySummary] = Field(default_factory=list)
    transaction_count: int = 0


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: TransactionType
    amount: Decimal
    category: Category
    subcategory: str | None
    description: str
    transaction_date: date
    created_at: datetime