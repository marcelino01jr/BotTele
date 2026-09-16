from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.enums import Category, TransactionType
from app.schemas.schemas import ParsedTransaction


def test_parsed_transaction_valid():
    parsed = ParsedTransaction(
        type="expense",
        amount="25000",
        category="Food",
        description="makan ayam geprek",
    )
    assert parsed.type == "expense"
    assert parsed.amount == Decimal("25000")
    assert parsed.category == "Food"
    assert parsed.transaction_date == date.today()


def test_parsed_transaction_full_fields():
    parsed = ParsedTransaction(
        type="income",
        amount="10000000",
        category="Salary",
        subcategory="Gaji bulanan",
        description="gaji",
        transaction_date=date(2026, 9, 1),
    )
    assert parsed.amount == Decimal("10000000")
    assert parsed.transaction_date == date(2026, 9, 1)


@pytest.mark.parametrize(
    "amount",
    ["0", "-100", "-0.01"],
)
def test_parsed_transaction_invalid_amount(amount):
    with pytest.raises(ValidationError):
        ParsedTransaction(
            type="expense",
            amount=amount,
            category="Food",
            description="makan",
        )


def test_parsed_transaction_invalid_category():
    with pytest.raises(ValidationError):
        ParsedTransaction(
            type="expense",
            amount="1000",
            category="Nope",
            description="makan",
        )


def test_parsed_transaction_invalid_type():
    with pytest.raises(ValidationError):
        ParsedTransaction(
            type="transfer",
            amount="1000",
            category="Food",
            description="makan",
        )


def test_parsed_transaction_empty_description():
    with pytest.raises(ValidationError):
        ParsedTransaction(
            type="expense",
            amount="1000",
            category="Food",
            description="",
        )


def test_parsed_transaction_empty_subcategory_becomes_none():
    parsed = ParsedTransaction(
        type="expense",
        amount="1000",
        category="Food",
        subcategory="  ",
        description="makan",
    )
    assert parsed.subcategory is None


def test_investment_type_allowed():
    parsed = ParsedTransaction(
        type="investment",
        amount="1000000",
        category="Investment",
        description="beli reksadana",
    )
    assert parsed.type == TransactionType.INVESTMENT


def test_category_enum_members():
    expected = {
        "Food",
        "Transport",
        "Housing",
        "Bills",
        "Shopping",
        "Entertainment",
        "Health",
        "Education",
        "Family",
        "Investment",
        "Salary",
        "Other",
    }
    assert set(Category) == {Category(m) for m in expected}