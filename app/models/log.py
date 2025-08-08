from typing import Optional
from sqlmodel import Field
from app.models import TimestampModel


class Log(TimestampModel, table=True):
    __tablename__ = "logs"

    log_id: Optional[int] = Field(default=None, primary_key=True)
    title: str


