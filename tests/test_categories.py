from app.models.enums import Category, EXPENSE_CATEGORIES, INCOME_CATEGORIES


def test_expense_categories():
    assert Category.FOOD in EXPENSE_CATEGORIES
    assert Category.TRANSPORT in EXPENSE_CATEGORIES
    assert Category.HOUSING in EXPENSE_CATEGORIES
    assert Category.BILLS in EXPENSE_CATEGORIES
    assert Category.SHOPPING in EXPENSE_CATEGORIES
    assert Category.ENTERTAINMENT in EXPENSE_CATEGORIES
    assert Category.HEALTH in EXPENSE_CATEGORIES
    assert Category.EDUCATION in EXPENSE_CATEGORIES
    assert Category.FAMILY in EXPENSE_CATEGORIES
    assert Category.OTHER in EXPENSE_CATEGORIES


def test_salary_and_investment_not_expense():
    assert Category.SALARY not in EXPENSE_CATEGORIES
    assert Category.INVESTMENT not in EXPENSE_CATEGORIES


def test_income_categories():
    assert Category.SALARY in INCOME_CATEGORIES
    assert Category.INVESTMENT in INCOME_CATEGORIES
    assert Category.OTHER in INCOME_CATEGORIES


def test_all_categories_covered():
    covered = EXPENSE_CATEGORIES | INCOME_CATEGORIES
    assert covered == set(Category)