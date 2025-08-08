from typing import Optional
from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TodoRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_completed: bool

    class Config:
        orm_mode = True


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None

    class Config:
        orm_mode = True
