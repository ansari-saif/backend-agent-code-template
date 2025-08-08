from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoRead, TodoUpdate
from app.core.database import get_session
from app.services.todo_service import (
    create_todo_service, delete_todo_service, get_todo_service, list_all_todo_service, update_todo_service
)

router = APIRouter()

@router.post("/", response_model=TodoRead, tags=["todo"])
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)):
    new_todo = create_todo_service(todo, session)
    return new_todo

@router.get("/{todo_id}", response_model=TodoRead, tags=["todo"])
def get_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = get_todo_service(todo_id, session)
    return todo

@router.put("/{todo_id}", response_model=TodoRead, tags=["todo"])
def update_todo(todo_id: int, todo_data: TodoUpdate, session: Session = Depends(get_session)):
    updated_todo = update_todo_service(todo_id, todo_data, session)
    return updated_todo

@router.delete("/{todo_id}", response_model=dict, tags=["todo"])
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    delete_todo_service(todo_id, session)
    return {"message": "Todo deleted successfully"}

@router.get("/", response_model=list[TodoRead], tags=["todo"])
def list_all_todo(session: Session = Depends(get_session)):
    todo = list_all_todo_service(session)
    return todo
