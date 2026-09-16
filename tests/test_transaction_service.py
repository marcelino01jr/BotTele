from datetime import date
from decimal import Decimal

from app.schemas.schemas import ParsedTransaction
from app.services.transaction_service import (
    create_transaction,
    list_transactions,
)
from tests.conftest import make_transaction, make_user


def test_create_transaction(db_session):
    user = make_user(db_session, telegram_id=1)
    parsed = ParsedTransaction(
        type="expense",
        amount="25000",
        category="Food",
        subcategory="Geprek",
        description="makan ayam geprek",
    )

    tx = create_transaction(db_session, user, parsed)

    assert tx.user_id == user.id
    assert tx.amount == Decimal("25000")
    assert tx.category == "Food"
    assert tx.transaction_date == date.today()


def test_list_transactions_scoped_to_user(db_session):
    user_a = make_user(db_session, telegram_id=100)
    user_b = make_user(db_session, telegram_id=200)

    make_transaction(db_session, user_a, amount="10000", description="milik A")
    make_transaction(db_session, user_a, amount="20000", description="milik A 2")
    make_transaction(db_session, user_b, amount="99999", description="milik B")

    txs_a = list_transactions(db_session, user_a)
    txs_b = list_transactions(db_session, user_b)

    assert len(txs_a) == 2
    assert len(txs_b) == 1
    assert all(tx.user_id == user_a.id for tx in txs_a)
    assert all(tx.user_id == user_b.id for tx in txs_b)
    assert txs_b[0].description == "milik B"


def test_list_transactions_date_filter(db_session):
    user = make_user(db_session, telegram_id=300)

    make_transaction(db_session, user, amount="1000", transaction_date=date(2026, 9, 1), description="awal bulan")
    make_transaction(db_session, user, amount="2000", transaction_date=date(2026, 9, 15), description="tengah bulan")
    make_transaction(db_session, user, amount="3000", transaction_date=date(2026, 9, 30), description="akhir bulan")

    result = list_transactions(
        db_session,
        user,
        start_date=date(2026, 9, 2),
        end_date=date(2026, 9, 20),
    )

    assert len(result) == 1
    assert result[0].description == "tengah bulan"