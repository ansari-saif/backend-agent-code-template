from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class TodoBase(SQLModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class TodoUpdate(TodoBase):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
