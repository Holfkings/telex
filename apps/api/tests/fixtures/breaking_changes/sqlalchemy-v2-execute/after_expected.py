from sqlalchemy.orm import Session
from sqlalchemy import select

User = object


def get_user(session: Session, user_id: int):
    return session.scalars(select(User).filter_by(id=user_id)).first()
