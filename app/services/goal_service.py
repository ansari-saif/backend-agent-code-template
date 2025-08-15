from typing import List, Optional
from sqlmodel import Session, select

from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate, StatusEnum, GoalTypeEnum


def create_goal(session: Session, goal_data: GoalCreate) -> Goal:
    goal = Goal.model_validate(goal_data)
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


def list_goals(session: Session, skip: int = 0, limit: int = 100, user_id: Optional[str] = None) -> List[Goal]:
    statement = select(Goal)
    if user_id:
        statement = statement.where(Goal.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()


def get_goal(session: Session, goal_id: int) -> Optional[Goal]:
    return session.get(Goal, goal_id)


def update_goal(session: Session, goal_id: int, update: GoalUpdate) -> Goal:
    goal = session.get(Goal, goal_id)
    if not goal:
        raise LookupError("Goal not found")
    data = update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(goal, field, value)
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


def delete_goal(session: Session, goal_id: int) -> None:
    goal = session.get(Goal, goal_id)
    if not goal:
        raise LookupError("Goal not found")
    session.delete(goal)
    session.commit()


def list_user_pending_goals(session: Session, user_id: str) -> List[Goal]:
    statement = select(Goal).where(Goal.user_id == user_id, Goal.status == StatusEnum.ACTIVE)
    return session.exec(statement).all()


def get_goal_hierarchy(session: Session, goal_id: int) -> Optional[Goal]:
    """Get a goal with its parent and child goals loaded."""
    statement = select(Goal).where(Goal.goal_id == goal_id)
    goal = session.exec(statement).first()
    if goal:
        # Load parent goal
        if goal.parent_goal_id:
            goal.parent_goal = session.get(Goal, goal.parent_goal_id)
        
        # Load child goals
        child_statement = select(Goal).where(Goal.parent_goal_id == goal_id)
        goal.child_goals = session.exec(child_statement).all()
    
    return goal


def list_goals_by_type(session: Session, user_id: str, goal_type: GoalTypeEnum) -> List[Goal]:
    """Get all goals of a specific type for a user."""
    statement = select(Goal).where(
        Goal.user_id == user_id,
        Goal.type == goal_type
    )
    return session.exec(statement).all()


def get_child_goals(session: Session, parent_goal_id: int) -> List[Goal]:
    """Get all child goals of a parent goal."""
    statement = select(Goal).where(Goal.parent_goal_id == parent_goal_id)
    return session.exec(statement).all()


def get_parent_goal(session: Session, child_goal_id: int) -> Optional[Goal]:
    """Get the parent goal of a child goal."""
    child_goal = session.get(Goal, child_goal_id)
    if child_goal and child_goal.parent_goal_id:
        return session.get(Goal, child_goal.parent_goal_id)
    return None

