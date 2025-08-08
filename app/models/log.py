from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Log(SQLModel, table=True):
    __tablename__ = "logs"

    log_id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


