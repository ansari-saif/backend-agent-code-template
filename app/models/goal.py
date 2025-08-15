from sqlmodel import Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import date
from app.schemas.goal import GoalTypeEnum, StatusEnum, PhaseEnum, PriorityEnum
from app.models import TimestampModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Goal(TimestampModel, table=True):
    __tablename__ = "goals"
    
    goal_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.telegram_id")
    parent_goal_id: Optional[int] = Field(default=None, foreign_key="goals.goal_id")
    type: GoalTypeEnum = GoalTypeEnum.MONTHLY
    description: str
    deadline: Optional[date] = None
    status: StatusEnum = StatusEnum.ACTIVE
    phase: PhaseEnum
    priority: PriorityEnum = PriorityEnum.MEDIUM
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="goals")
    tasks: List["Task"] = Relationship(back_populates="goal")
    parent_goal: Optional["Goal"] = Relationship(
        back_populates="child_goals",
        sa_relationship_kwargs={"remote_side": "Goal.goal_id"}
    )
    child_goals: List["Goal"] = Relationship(back_populates="parent_goal")