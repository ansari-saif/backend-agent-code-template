from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.models.goal import Goal, GoalCreate, GoalUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=Goal, status_code=status.HTTP_201_CREATED)
def create_goal(goal: GoalCreate, session: Session = Depends(get_session)):
    """Create a new goal."""
    # Verify user exists
    user = session.get(User, goal.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_goal = Goal.model_validate(goal)
    session.add(db_goal)
    session.commit()
    session.refresh(db_goal)
    return db_goal

@router.get("/", response_model=List[Goal])
def read_goals(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get all goals with optional user filtering."""
    statement = select(Goal)
    if user_id:
        statement = statement.where(Goal.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    goals = session.exec(statement).all()
    return goals

@router.get("/{goal_id}", response_model=Goal)
def read_goal(goal_id: int, session: Session = Depends(get_session)):
    """Get a specific goal by ID."""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    return goal

@router.put("/{goal_id}", response_model=Goal)
def update_goal(goal_id: int, goal_update: GoalUpdate, session: Session = Depends(get_session)):
    """Update a goal."""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    goal_data = goal_update.model_dump(exclude_unset=True)
    for field, value in goal_data.items():
        setattr(goal, field, value)
    
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, session: Session = Depends(get_session)):
    """Delete a goal."""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    session.delete(goal)
    session.commit()
    return None

@router.get("/user/{user_id}", response_model=List[Goal])
def get_user_goals(user_id: str, session: Session = Depends(get_session)):
    """Get all goals for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    statement = select(Goal).where(Goal.user_id == user_id)
    goals = session.exec(statement).all()
    return goals

@router.get("/user/{user_id}/pending", response_model=List[Goal])
def get_user_pending_goals(user_id: str, session: Session = Depends(get_session)):
    """Get all pending goals for a specific user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    statement = select(Goal).where(
        Goal.user_id == user_id,
        Goal.status.in_(["Not Started", "In Progress"])
    )
    goals = session.exec(statement).all()
    return goals 