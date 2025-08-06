from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time
from enum import Enum


class TimezoneEnum(str, Enum):
    UTC = "UTC"
    EST = "EST"
    PST = "PST"
    CST = "CST"
    MST = "MST"
    IST = "IST"


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


class UserBase(BaseModel):
    telegram_id: str
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


class UserResponse(UserBase):
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    birthday: Optional[date] = None
    timezone: Optional[TimezoneEnum] = None
    current_phase: Optional[PhaseEnum] = None
    quit_job_target: Optional[date] = None
    onboarding_complete: Optional[bool] = None
    morning_time: Optional[time] = None
    energy_profile: Optional[EnergyProfileEnum] = None