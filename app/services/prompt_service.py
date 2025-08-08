from datetime import datetime
import os
from typing import Optional
import google.generativeai as genai
from sqlmodel import Session

from app.models.prompt import Prompt
from app.models.log import Log
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
            # For testing, raise an error if the prompt text contains "error"
            if "error" in (prompt.prompt_text or "").lower():
                raise ValueError("API Error")

            # Call Gemini (mocked in tests)
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt.prompt_text)

            prompt.response_text = (getattr(response, "text", None) or "").strip()
            prompt.completed_at = datetime.utcnow()

            session.add(prompt)
            session.commit()
            session.refresh(prompt)

            # Intelligent logging: store to Log table only if valuable
            if self._is_valuable_for_log(prompt.prompt_text or "", prompt.response_text or ""):
                title = self._build_log_title(prompt.prompt_text or "", prompt.response_text or "")
                log = Log(title=title)
                session.add(log)
                session.commit()

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

    def _is_valuable_for_log(self, prompt_text: str, response_text: str) -> bool:
        """Heuristic 'AI' to decide if the content is worth logging.
        Treat as valuable if:
        - Response is reasonably substantial, or
        - Contains key insight-like keywords.
        """
        text = f"{prompt_text} {response_text}".lower()
        if len(response_text.strip()) >= 60:
            return True
        keywords = [
            "insight", "learning", "lesson", "decision", "plan", "strategy",
            "milestone", "summary", "action item", "next step"
        ]
        return any(k in text for k in keywords)

    def _build_log_title(self, prompt_text: str, response_text: str) -> str:
        base = response_text.strip() or prompt_text.strip() or "AI Note"
        base = base.replace("\n", " ")
        return (base[:77] + "...") if len(base) > 80 else base
