from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date, time
from enum import Enum


class TimezoneEnum(str, Enum):
    UTC = "UTC"
    EST = "EST"
    PST = "PST"
    CST = "CST"
    MST = "MST"


class PhaseEnum(str, Enum):
    RESEARCH = "Research"
    MVP = "MVP"
    GROWTH = "Growth"
    SCALE = "Scale"
    TRANSITION = "Transition"


class EnergyProfileEnum(str, Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    EVENING = "Evening"


class UserBase(SQLModel):
    telegram_id: str = Field(primary_key=True)
    name: str
    birthday: Optional[date] = None
    timezone: TimezoneEnum = TimezoneEnum.UTC
    current_phase: PhaseEnum = PhaseEnum.RESEARCH
    quit_job_target: Optional[date] = None
    onboarding_complete: bool = False
    morning_time: Optional[time] = None
    energy_profile: EnergyProfileEnum = EnergyProfileEnum.MORNING


class UserCreate(UserBase):
    pass


class User(UserBase, table=True):
    __tablename__ = "users"
    
    # Relationships
    goals: List["Goal"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    progress_logs: List["ProgressLog"] = Relationship(back_populates="user")
    ai_context: Optional["AIContext"] = Relationship(back_populates="user")
    job_metrics: Optional["JobMetrics"] = Relationship(back_populates="user")


class UserUpdate(SQLModel):
    name: Optional[str] = None
    birthday: Optional[date] = None
    timezone: Optional[TimezoneEnum] = None
    current_phase: Optional[PhaseEnum] = None
    quit_job_target: Optional[date] = None
    onboarding_complete: Optional[bool] = None
    morning_time: Optional[time] = None
    energy_profile: Optional[EnergyProfileEnum] = None 