from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptResponse, PromptUpdate
from app.services.prompt_service import PromptService

router = APIRouter()
prompt_service = PromptService()

@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    session: Session = Depends(get_session)
) -> Prompt:
    try:
        # First create the prompt
        prompt = await prompt_service.create_prompt(session, prompt_data)
        # Then process it with Gemini
        processed_prompt = await prompt_service.process_prompt(session, prompt)
        return processed_prompt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/user/{user_id}", response_model=list[PromptResponse])
async def get_user_prompts(
    user_id: str,
    session: Session = Depends(get_session)
) -> list[Prompt]:
    """Get all prompts for a specific user"""
    return await prompt_service.get_user_prompts(session, user_id)

@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    session: Session = Depends(get_session)
) -> Prompt:
    try:
        return await prompt_service.get_prompt(session, prompt_id)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    prompt_update: PromptUpdate,
    session: Session = Depends(get_session)
) -> Prompt:
    try:
        return await prompt_service.update_prompt(session, prompt_id, prompt_update)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
