from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import User


def get_or_create_user(
    db: Session,
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
) -> User:
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        return user

    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user