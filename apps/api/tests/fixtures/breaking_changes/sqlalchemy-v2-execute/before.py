from sqlalchemy.orm import Session
User = object

def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()
