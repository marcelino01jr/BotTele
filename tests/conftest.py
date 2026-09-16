import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.tables import Transaction, User


@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def make_user(
    session,
    telegram_id: int = 123,
    first_name: str | None = "Marcel",
    username: str | None = None,
) -> User:
    user = User(telegram_id=telegram_id, first_name=first_name, username=username)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def make_transaction(
    session,
    user: User,
    type: str = "expense",
    amount: str = "25000",
    category: str = "Food",
    transaction_date=None,
    description: str = "makan",
) -> Transaction:
    from datetime import date

    tx = Transaction(
        user_id=user.id,
        type=type,
        amount=amount,
        category=category,
        subcategory=None,
        description=description,
        transaction_date=transaction_date or date.today(),
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx