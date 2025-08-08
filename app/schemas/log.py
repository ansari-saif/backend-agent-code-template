from datetime import datetime
from pydantic import BaseModel, Field


class LogBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class LogCreate(LogBase):
    pass


class LogResponse(LogBase):
    log_id: int
    created_at: datetime

    class Config:
        from_attributes = True


