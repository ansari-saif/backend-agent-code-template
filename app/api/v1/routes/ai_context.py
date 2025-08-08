from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.models.ai_context import AIContext
from app.schemas.ai_context import AIContextCreate, AIContextResponse, AIContextUpdate
from app.services import ai_context_service

router = APIRouter()


@router.post("/", response_model=AIContextResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_context(
    ai_context_data: AIContextCreate,
    session: Session = Depends(get_session),
) -> AIContext:
    try:
        return await ai_context_service.create_ai_context(session, ai_context_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{context_id}", response_model=AIContextResponse)
def get_ai_context(
    context_id: int,
    session: Session = Depends(get_session),
) -> AIContext:
    try:
        return ai_context_service.get_ai_context(session, context_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}", response_model=AIContextResponse)
def get_ai_context_by_user(
    user_id: str,
    session: Session = Depends(get_session),
) -> AIContext:
    try:
        return ai_context_service.get_ai_context_by_user(session, user_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{context_id}", response_model=AIContextResponse)
def update_ai_context(
    context_id: int,
    ai_context_data: AIContextUpdate,
    session: Session = Depends(get_session),
) -> AIContext:
    try:
        return ai_context_service.update_ai_context(session, context_id, ai_context_data)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_context(
    context_id: int,
    session: Session = Depends(get_session),
) -> None:
    try:
        ai_context_service.delete_ai_context(session, context_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))