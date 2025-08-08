from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class DayLogBase(BaseModel):
    date: date
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Optional[str] = Field(default=None, max_length=2000)
    highlights: Optional[str] = Field(default=None, max_length=2000)
    challenges: Optional[str] = Field(default=None, max_length=2000)
    learnings: Optional[str] = Field(default=None, max_length=2000)
    gratitude: Optional[str] = Field(default=None, max_length=2000)
    tomorrow_plan: Optional[str] = Field(default=None, max_length=2000)
    weather: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=100)

    model_config = {"validate_assignment": True}

    def model_post_init(self, __context):
        if self.end_time and self.start_time:
            if self.end_time < self.start_time:
                raise ValueError("end_time must be after start_time")
        current_date = date.today()
        if self.date > current_date:
            raise ValueError("date cannot be in the future")


class DayLogCreate(DayLogBase):
    user_id: str


class DayLogResponse(DayLogBase):
    log_id: int
    user_id: str

    class Config:
        from_attributes = True


class DayLogUpdate(BaseModel):
    date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    highlights: Optional[str] = None
    challenges: Optional[str] = None
    learnings: Optional[str] = None
    gratitude: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    weather: Optional[str] = None
    location: Optional[str] = None
