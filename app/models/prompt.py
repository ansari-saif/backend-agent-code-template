from datetime import datetime
from typing import Optional
from sqlmodel import Field
import uuid
from app.models import TimestampModel

class Prompt(TimestampModel, table=True):
    __tablename__ = "prompts"
    
    prompt_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(..., index=True)
    prompt_text: str = Field(...)
    response_text: Optional[str] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
