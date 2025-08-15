from pydantic import BaseModel, Field
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


class GoalBase(BaseModel):
    user_id: str
    parent_goal_id: Optional[int] = None
    type: GoalTypeEnum
    description: str
    deadline: Optional[date] = None
    status: StatusEnum = StatusEnum.ACTIVE
    phase: PhaseEnum
    priority: PriorityEnum = PriorityEnum.MEDIUM
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class GoalCreate(GoalBase):
    pass


class GoalResponse(GoalBase):
    goal_id: int

    class Config:
        from_attributes = True


class GoalHierarchyResponse(GoalResponse):
    child_goals: List["GoalResponse"] = []
    parent_goal: Optional["GoalResponse"] = None

    class Config:
        from_attributes = True


class GoalUpdate(BaseModel):
    parent_goal_id: Optional[int] = None
    type: Optional[GoalTypeEnum] = None
    description: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[StatusEnum] = None
    phase: Optional[PhaseEnum] = None
    priority: Optional[PriorityEnum] = None
    completion_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)