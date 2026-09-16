from enum import StrEnum


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    INVESTMENT = "investment"


class Category(StrEnum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    HOUSING = "Housing"
    BILLS = "Bills"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    HEALTH = "Health"
    EDUCATION = "Education"
    FAMILY = "Family"
    INVESTMENT = "Investment"
    SALARY = "Salary"
    OTHER = "Other"


EXPENSE_CATEGORIES = {
    Category.FOOD,
    Category.TRANSPORT,
    Category.HOUSING,
    Category.BILLS,
    Category.SHOPPING,
    Category.ENTERTAINMENT,
    Category.HEALTH,
    Category.EDUCATION,
    Category.FAMILY,
    Category.OTHER,
}

INCOME_CATEGORIES = {
    Category.SALARY,
    Category.INVESTMENT,
    Category.OTHER,
}