from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse, GoalHierarchyResponse, StatusEnum, GoalTypeEnum
from app.services import goal_service

router = APIRouter()

@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(goal: GoalCreate, session: Session = Depends(get_session)):
    """Create a new goal."""
    # Verify user exists
    user = session.get(User, goal.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify parent goal exists if specified
    if goal.parent_goal_id:
        parent_goal = session.get(Goal, goal.parent_goal_id)
        if not parent_goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent goal not found"
            )
    
    db_goal = Goal.model_validate(goal)
    session.add(db_goal)
    session.commit()
    session.refresh(db_goal)
    return db_goal

@router.get("/", response_model=List[GoalResponse])
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

@router.get("/{goal_id}", response_model=GoalResponse)
def read_goal(goal_id: int, session: Session = Depends(get_session)):
    """Get a specific goal by ID."""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    return goal

@router.get("/{goal_id}/hierarchy", response_model=GoalHierarchyResponse)
def read_goal_hierarchy(goal_id: int, session: Session = Depends(get_session)):
    """Get a goal with its parent and child goals."""
    goal = goal_service.get_goal_hierarchy(session, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    return goal

@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, goal_update: GoalUpdate, session: Session = Depends(get_session)):
    """Update a goal."""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Verify parent goal exists if specified
    if goal_update.parent_goal_id:
        parent_goal = session.get(Goal, goal_update.parent_goal_id)
        if not parent_goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent goal not found"
            )
    
    goal_data = goal_update.model_dump(exclude_unset=True)
    for field, value in goal_data.items():
        setattr(goal, field, value)
    
    session.add(goal)
    session.commit()
    session.refresh(goal)
    
    # Update parent goal progress if this goal has a parent
    if goal.parent_goal_id:
        goal_service.update_goal_hierarchy_progress(session, goal.parent_goal_id)
    
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
    
    # Store parent goal ID before deletion for progress update
    parent_goal_id = goal.parent_goal_id
    
    session.delete(goal)
    session.commit()
    
    # Update parent goal progress if needed
    if parent_goal_id:
        goal_service.update_goal_hierarchy_progress(session, parent_goal_id)
    
    return None

@router.get("/user/{user_id}", response_model=List[GoalResponse])
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

@router.get("/user/{user_id}/pending", response_model=List[GoalResponse])
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
        Goal.status == StatusEnum.ACTIVE
    )
    goals = session.exec(statement).all()
    return goals

@router.get("/user/{user_id}/type/{goal_type}", response_model=List[GoalResponse])
def get_user_goals_by_type(user_id: str, goal_type: GoalTypeEnum, session: Session = Depends(get_session)):
    """Get all goals of a specific type for a user."""
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    goals = goal_service.list_goals_by_type(session, user_id, goal_type)
    return goals

@router.get("/{goal_id}/children", response_model=List[GoalResponse])
def get_child_goals(goal_id: int, session: Session = Depends(get_session)):
    """Get all child goals of a parent goal."""
    # Verify parent goal exists
    parent_goal = session.get(Goal, goal_id)
    if not parent_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent goal not found"
        )
    
    child_goals = goal_service.get_child_goals(session, goal_id)
    return child_goals

@router.get("/{goal_id}/parent", response_model=GoalResponse)
def get_parent_goal(goal_id: int, session: Session = Depends(get_session)):
    """Get the parent goal of a child goal."""
    # Verify child goal exists
    child_goal = session.get(Goal, goal_id)
    if not child_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    parent_goal = goal_service.get_parent_goal(session, goal_id)
    if not parent_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parent goal found"
        )
    
    return parent_goal
