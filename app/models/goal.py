from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date
from enum import Enum


class GoalTypeEnum(str, Enum):
    YEARLY = "Yearly"
    QUARTERLY = "Quarterly"
    MONTHLY = "Monthly"
    WEEKLY = "Weekly"


class StatusEnum(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    PAUSED = "Paused"


class PhaseEnum(str, Enum):
    RESEARCH = "Research"
    MVP = "MVP"
    GROWTH = "Growth"
    SCALE = "Scale"
    TRANSITION = "Transition"


class PriorityEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class GoalBase(SQLModel):
    user_id: str = Field(foreign_key="users.telegram_id")
    type: GoalTypeEnum
    description: str
    deadline: Optional[date] = None
    status: StatusEnum = StatusEnum.ACTIVE
    phase: PhaseEnum
    priority: PriorityEnum = PriorityEnum.MEDIUM
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class GoalCreate(GoalBase):
    pass


class Goal(GoalBase, table=True):
    __tablename__ = "goals"
    
    goal_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="goals")
    tasks: List["Task"] = Relationship(back_populates="goal")


class GoalUpdate(SQLModel):
    type: Optional[GoalTypeEnum] = None
    description: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[StatusEnum] = None
    phase: Optional[PhaseEnum] = None
    priority: Optional[PriorityEnum] = None
    completion_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0) 