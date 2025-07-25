from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.models.user import User, UserCreate, UserUpdate

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """Create a new user."""
    # Check if user already exists
    existing_user = session.get(User, user.telegram_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this telegram_id already exists"
        )
    
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """Get all users with pagination."""
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users

@router.get("/{telegram_id}", response_model=User)
def read_user(telegram_id: str, session: Session = Depends(get_session)):
    """Get a specific user by telegram_id."""
    user = session.get(User, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{telegram_id}", response_model=User)
def update_user(telegram_id: str, user_update: UserUpdate, session: Session = Depends(get_session)):
    """Update a user."""
    user = session.get(User, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data = user_update.model_dump(exclude_unset=True)
    for field, value in user_data.items():
        setattr(user, field, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.delete("/{telegram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(telegram_id: str, session: Session = Depends(get_session)):
    """Delete a user."""
    user = session.get(User, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    session.delete(user)
    session.commit()
    return None

@router.get("/{telegram_id}/profile", response_model=User)
def get_user_profile(telegram_id: str, session: Session = Depends(get_session)):
    """Get user profile with all relationships."""
    statement = select(User).where(User.telegram_id == telegram_id)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user 