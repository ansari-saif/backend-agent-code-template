from typing import List, Optional
from sqlmodel import Session, select

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(session: Session, user_data: UserCreate) -> User:
    existing_user = session.get(User, user_data.telegram_id)
    if existing_user:
        raise ValueError("User with this telegram_id already exists")

    user = User(
        telegram_id=user_data.telegram_id,
        name=user_data.name,
        birthday=user_data.birthday,
        timezone=user_data.timezone,
        current_phase=user_data.current_phase,
        quit_job_target=user_data.quit_job_target,
        onboarding_complete=user_data.onboarding_complete,
        morning_time=user_data.morning_time,
        energy_profile=user_data.energy_profile,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_users(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_user(session: Session, telegram_id: str) -> Optional[User]:
    return session.get(User, telegram_id)


def update_user(session: Session, telegram_id: str, update: UserUpdate) -> User:
    user = session.get(User, telegram_id)
    if not user:
        raise LookupError("User not found")

    user_data = update.model_dump(exclude_unset=True)
    for field, value in user_data.items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, telegram_id: str) -> None:
    user = session.get(User, telegram_id)
    if not user:
        raise LookupError("User not found")
    session.delete(user)
    session.commit()


def get_user_profile(session: Session, telegram_id: str) -> User:
    statement = select(User).where(User.telegram_id == telegram_id)
    user = session.exec(statement).first()
    if not user:
        raise LookupError("User not found")
    return user


