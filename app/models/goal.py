from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date
from app.schemas.goal import GoalTypeEnum, StatusEnum, PhaseEnum, PriorityEnum


class Goal(SQLModel, table=True):
    __tablename__ = "goals"
    
    goal_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.telegram_id")
    type: GoalTypeEnum
    description: str
    deadline: Optional[date] = None
    status: StatusEnum = StatusEnum.ACTIVE
    phase: PhaseEnum
    priority: PriorityEnum = PriorityEnum.MEDIUM
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="goals")
    tasks: List["Task"] = Relationship(back_populates="goal")