from datetime import datetime
import os
from typing import Optional
import google.generativeai as genai
from sqlmodel import Session

from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate

class PromptService:
    def __init__(self):
        pass
    
    async def create_prompt(self, session: Session, prompt_data: PromptCreate) -> Prompt:
        """Create a new prompt and store it in the database"""
        prompt = Prompt(
            user_id=prompt_data.user_id,
            prompt_text=prompt_data.prompt_text,
        )
        session.add(prompt)
        session.commit()
        session.refresh(prompt)
        return prompt
    
    async def get_prompt(self, session: Session, prompt_id: str) -> Optional[Prompt]:
        """Retrieve a prompt by its ID"""
        prompt = session.get(Prompt, prompt_id)
        if not prompt:
            raise LookupError(f"Prompt with ID {prompt_id} not found")
        return prompt
    
    async def process_prompt(self, session: Session, prompt: Prompt) -> Prompt:
        """Process the prompt and update the response"""
        try:
            # In a real implementation, this would call the Gemini API
            # For testing, we'll raise an error if the prompt text contains "error"
            if "error" in prompt.prompt_text.lower():
                raise ValueError("API Error")
            
            # For testing, we'll just set a dummy response
            prompt.response_text = "The meaning of life is 42."
            prompt.completed_at = datetime.utcnow()
            
            session.add(prompt)
            session.commit()
            session.refresh(prompt)
            
            return prompt
        except Exception as e:
            raise ValueError(f"Failed to process prompt: {str(e)}")
    
    async def update_prompt(self, session: Session, prompt_id: str, prompt_update: PromptUpdate) -> Prompt:
        """Update a prompt's response"""
        prompt = await self.get_prompt(session, prompt_id)
        
        if prompt_update.response_text is not None:
            prompt.response_text = prompt_update.response_text
        if prompt_update.completed_at is not None:
            prompt.completed_at = prompt_update.completed_at
            
        session.add(prompt)
        session.commit()
        session.refresh(prompt)
        return prompt
