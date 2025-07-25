from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models.todo import Todo, TodoCreate, TodoUpdate

router = APIRouter()

@router.post("/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)):
    """Create a new todo."""
    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo

@router.get("/", response_model=List[Todo])
def read_todos(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """Get all todos with pagination."""
    statement = select(Todo).offset(skip).limit(limit)
    todos = session.exec(statement).all()
    return todos

@router.get("/{todo_id}", response_model=Todo)
def read_todo(todo_id: int, session: Session = Depends(get_session)):
    """Get a specific todo by ID."""
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo

@router.put("/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate, session: Session = Depends(get_session)):
    """Update a todo."""
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    todo_data = todo_update.model_dump(exclude_unset=True)
    for field, value in todo_data.items():
        setattr(todo, field, value)
    
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    """Delete a todo."""
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    session.delete(todo)
    session.commit()
    return None
