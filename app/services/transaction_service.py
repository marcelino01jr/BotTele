from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import Transaction, User
from app.schemas.schemas import ParsedTransaction, TransactionOut


def _as_decimal(value) -> Decimal:
    return Decimal(value)


def create_transaction(
    db: Session,
    user: User,
    parsed: ParsedTransaction,
) -> Transaction:
    tx = Transaction(
        user_id=user.id,
        type=parsed.type,
        amount=_as_decimal(parsed.amount),
        category=parsed.category,
        subcategory=parsed.subcategory,
        description=parsed.description,
        transaction_date=parsed.transaction_date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def list_transactions(
    db: Session,
    user: User,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Transaction]:
    query = select(Transaction).where(Transaction.user_id == user.id)
    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    query = query.order_by(Transaction.transaction_date.asc(), Transaction.id.asc())
    return list(db.scalars(query))


def to_out(tx: Transaction) -> TransactionOut:
    return TransactionOut.model_validate(tx)